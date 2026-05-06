from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import intake_high_signal_transcripts as intake  # noqa: E402


VALID_TRANSCRIPT = """
Acme Corp Q4 2025 Earnings Call
Operator: Good afternoon and welcome to the earnings call.
Prepared Remarks
CEO: We expect revenue to improve next quarter and we raised guidance.
Question-and-Answer
Analyst: Can you discuss margin outlook and customer demand?
CFO: We expect revenue of between 10 and 12 billion plus or minus 2 percent.
""" + ("Management answer with earnings call detail. " * 180)


def test_default_tickers_are_exact_25_company_benchmark() -> None:
    expected = {
        "NVDA",
        "MSFT",
        "GOOGL",
        "AMZN",
        "META",
        "AAPL",
        "AMD",
        "ASML",
        "TSM",
        "AVGO",
        "CRM",
        "SNOW",
        "HUBS",
        "NOW",
        "DDOG",
        "NET",
        "MDB",
        "PANW",
        "CRWD",
        "TSLA",
        "SHOP",
        "UBER",
        "RBLX",
        "COIN",
        "PLTR",
    }
    assert set(intake.TARGET_TICKERS) == expected
    assert len(intake.TARGET_TICKERS) == 25
    assert "TSLA" in intake.TARGET_TICKERS


def test_default_latest_calls_plans_100_calls() -> None:
    args = intake.parse_args(["--dry-run"])
    planned = intake.plan_cases(
        tickers=intake.normalize_tickers(args),
        periods=intake.discovery_periods(args),
        configured_sources={},
        latest_calls=args.latest_calls,
        source_mode=args.source,
    )
    assert args.latest_calls == 4
    assert len(planned) == 100
    assert len({case.ticker for case in planned}) == 25
    assert sum(1 for case in planned if case.ticker == "TSLA") == 4


def test_cli_argument_parsing_and_ticker_file(tmp_path: Path) -> None:
    ticker_file = tmp_path / "tickers.txt"
    ticker_file.write_text("amd\nNET\nAMD\n", encoding="utf-8")
    args = intake.parse_args(["--ticker-file", str(ticker_file), "--tickers", "tsla", "--years", "2025", "--quarters", "Q4", "--dry-run"])
    assert intake.normalize_tickers(args) == ["TSLA", "AMD", "NET"]
    planned = intake.plan_cases(
        tickers=intake.normalize_tickers(args),
        periods=intake.discovery_periods(args),
        configured_sources={},
        latest_calls=1,
        source_mode=args.source,
    )
    assert [case.case_id for case in planned] == ["TSLA_2025_Q4", "AMD_2025_Q4", "NET_2025_Q4"]


def test_source_url_file_drives_manual_sources(tmp_path: Path) -> None:
    source_file = tmp_path / "sources.csv"
    source_file.write_text(
        "ticker,fiscal_year,quarter,source_url,company_name,notes\n"
        "PLTR,2025,Q4,https://example.com/pltr-q4.txt,Palantir,fixture public text\n",
        encoding="utf-8",
    )
    sources = intake.load_manual_source_urls(source_file)
    assert "PLTR_2025_Q4" in sources
    planned = intake.plan_cases(
        tickers=["PLTR"],
        periods=[("2025", "Q4")],
        configured_sources=sources,
        latest_calls=1,
        source_mode="existing_config",
    )
    assert planned[0].source_url == "https://example.com/pltr-q4.txt"
    assert planned[0].source_type == "text"


def test_folder_creation_provenance_schema_and_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(intake, "fetch_url", lambda url, timeout: (b"<html>transcript</html>", "text/html"))
    monkeypatch.setattr(intake, "extract_html_text", lambda content, url: VALID_TRANSCRIPT)
    case = intake.PlannedCase(
        case_id="TSLA_2025_Q4",
        ticker="TSLA",
        fiscal_year="2025",
        quarter="Q4",
        source_url="https://example.com/tsla-transcript",
        source_type="html",
        notes="fixture source",
    )
    row = intake.write_case_outputs(
        case=case,
        output_root=tmp_path,
        overwrite=False,
        min_chars=500,
        require_markers=True,
        timeout=5,
    )
    assert row["review_ready"] is True
    case_dir = tmp_path / "TSLA_2025_Q4"
    provenance = json.loads((case_dir / "metadata" / "provenance.json").read_text(encoding="utf-8"))
    assert set(
        [
            "case_id",
            "ticker",
            "company_name",
            "fiscal_year",
            "fiscal_quarter",
            "source_url",
            "source_type",
            "downloaded_at",
            "raw_transcript_path",
            "transcript_char_count",
            "validation_status",
            "quality_flags",
            "notes",
        ]
    ).issubset(provenance)
    assert (case_dir / "processed" / "transcript_sectioned.json").exists()
    assert (case_dir / "labels" / "human_labeling_packet.md").exists()
    assert (case_dir / "labels" / "weak_label_candidates.jsonl").exists()
    intake.write_manifest(tmp_path, [row])
    corpus_manifest = intake.update_global_corpus_manifest(tmp_path, [row], manifest_path=tmp_path / "corpus_manifest.csv")
    assert (tmp_path / "high_signal_manifest.csv").exists()
    assert corpus_manifest.exists()
    manifest = json.loads((tmp_path / "high_signal_manifest.json").read_text(encoding="utf-8"))
    assert manifest[0]["case_id"] == "TSLA_2025_Q4"


def test_invalid_manual_placeholder_is_not_review_ready(tmp_path: Path) -> None:
    case = intake.PlannedCase(
        case_id="HUBS_2026_Q4",
        ticker="HUBS",
        fiscal_year="2026",
        quarter="Q4",
        source_url="",
        source_type="manual_placeholder",
        notes="manual required",
    )
    row = intake.write_case_outputs(
        case=case,
        output_root=tmp_path,
        overwrite=False,
        min_chars=5000,
        require_markers=True,
        timeout=5,
    )
    assert row["status"] == "failed"
    assert row["review_ready"] is False
    status = json.loads((tmp_path / "HUBS_2026_Q4" / "outputs" / "intake_status.json").read_text(encoding="utf-8"))
    assert status["review_ready"] is False
    assert "manual_transcript_required" in status["quality_flags"]


def test_no_raw_overwrite_by_default(tmp_path: Path) -> None:
    case_dir = tmp_path / "AMD_2025_Q4" / "raw"
    case_dir.mkdir(parents=True)
    (case_dir / "transcript.txt").write_text("existing raw transcript", encoding="utf-8")
    case = intake.PlannedCase(
        case_id="AMD_2025_Q4",
        ticker="AMD",
        fiscal_year="2025",
        quarter="Q4",
        source_url="",
        source_type="manual_placeholder",
        notes="manual required",
    )
    with pytest.raises(intake.IntakeError, match="overwrite is false"):
        intake.write_case_outputs(
            case=case,
            output_root=tmp_path,
            overwrite=False,
            min_chars=5000,
            require_markers=True,
            timeout=5,
        )


def test_dry_run_does_not_write(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = intake.main(
        [
            "--tickers",
            "TSLA",
            "AMD",
            "--years",
            "2025",
            "--quarters",
            "Q4",
            "--output-root",
            str(tmp_path),
            "--max-cases-per-ticker",
            "1",
            "--dry-run",
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["dry_run"] is True
    assert payload["cases_discovered"] == 2
    assert payload["target_calls"] == 2
    assert not (tmp_path / "high_signal_manifest.csv").exists()


def test_parser_splits_prepared_and_qa_fixture() -> None:
    parsed = intake.parse_transcript(VALID_TRANSCRIPT)
    section_names = [section["name"] for section in parsed["sections"]]
    assert "prepared_remarks" in section_names
    assert "question_and_answer" in section_names
    assert any(turn["speaker"] == "Analyst" for turn in parsed["speaker_turns"])
