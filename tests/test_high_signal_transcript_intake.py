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


def test_cli_argument_parsing_and_ticker_file(tmp_path: Path) -> None:
    ticker_file = tmp_path / "tickers.txt"
    ticker_file.write_text("amd\nNET\nAMD\n", encoding="utf-8")
    args = intake.parse_args(["--ticker-file", str(ticker_file), "--tickers", "tsla", "--years", "2025", "--quarters", "Q4", "--dry-run"])
    assert intake.normalize_tickers(args) == ["TSLA", "AMD", "NET"]
    planned = intake.plan_cases(
        tickers=intake.normalize_tickers(args),
        years=args.years,
        quarters=args.quarters,
        configured_sources={},
        max_cases_per_ticker=1,
        source_mode=args.source,
    )
    assert [case.case_id for case in planned] == ["TSLA_2025_Q4", "AMD_2025_Q4", "NET_2025_Q4"]


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
    assert (tmp_path / "high_signal_manifest.csv").exists()
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
    assert not (tmp_path / "high_signal_manifest.csv").exists()
