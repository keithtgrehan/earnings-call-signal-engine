from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import discover_high_signal_transcript_sources as discovery  # noqa: E402
import intake_high_signal_transcripts as intake  # noqa: E402


LONG_TRANSCRIPT = (
    "NVIDIA Corporation Q4 2026 earnings call transcript\n"
    "Operator: Welcome to the earnings call.\n"
    "Prepared remarks\n"
    "Question-and-Answer\n"
    "Analyst: Can you discuss Q4 FY2026 demand?\n"
    + ("NVIDIA Q4 2026 conference call prepared remarks and analyst answer. " * 120)
)


def test_query_generation_uses_precise_case_terms() -> None:
    case = discovery.TargetCase(
        case_id="NVDA_2026_Q4",
        ticker="NVDA",
        company_name="NVIDIA Corporation",
        fiscal_year="2026",
        quarter="Q4",
        company_domain="nvidia.com",
    )
    queries = discovery.generate_queries(case)
    assert "NVIDIA Corporation 2026 Q4 earnings call transcript" in queries
    assert "NVDA 2026 Q4 earnings call transcript" in queries
    assert "site:investor.nvidia.com NVDA earnings call transcript" in queries
    assert "site:sec.gov NVDA 8-K earnings call transcript" in queries


def test_target_case_detection_matches_25_by_4() -> None:
    cases = discovery.build_target_cases(
        tickers=list(intake.TARGET_TICKERS),
        years=["2024", "2025", "2026"],
        quarters=["Q1", "Q2", "Q3", "Q4"],
        max_cases_per_ticker=4,
    )
    assert len(cases) == 100
    assert {case.ticker for case in cases} == set(intake.TARGET_TICKERS)
    assert [case.case_id for case in cases if case.ticker == "NVDA"] == [
        "NVDA_2026_Q4",
        "NVDA_2026_Q3",
        "NVDA_2026_Q2",
        "NVDA_2026_Q1",
    ]


def test_candidate_url_parsing_from_csv_and_json(tmp_path: Path) -> None:
    cases = discovery.build_target_cases(tickers=["NVDA"], years=["2026"], quarters=["Q4"], max_cases_per_ticker=1)
    cases_by_id = {case.case_id: case for case in cases}
    csv_path = tmp_path / "results.csv"
    csv_path.write_text(
        "case_id,ticker,fiscal_year,quarter,url,title\n"
        "NVDA_2026_Q4,NVDA,2026,Q4,https://investor.nvidia.com/transcript.txt,NVIDIA transcript\n",
        encoding="utf-8",
    )
    json_path = tmp_path / "results.json"
    json_path.write_text(
        json.dumps({"results": [{"case_id": "NVDA_2026_Q4", "link": "https://sec.gov/example", "snippet": "8-K transcript"}]}),
        encoding="utf-8",
    )
    rows = discovery.rows_from_file(csv_path) + discovery.rows_from_file(json_path)
    candidates = discovery.candidates_from_rows(rows, cases_by_id)
    assert [candidate.source_url for candidate in candidates["NVDA_2026_Q4"]] == [
        "https://investor.nvidia.com/transcript.txt",
        "https://sec.gov/example",
    ]


def test_robots_disallowed_rejects_without_download() -> None:
    case = discovery.TargetCase("NVDA_2026_Q4", "NVDA", "NVIDIA Corporation", "2026", "Q4", "nvidia.com")
    candidate = discovery.CandidateSource(source_url="https://investor.nvidia.com/transcript.txt")
    calls = {"download": 0}

    def downloader(url: str, timeout: int) -> tuple[bytes, str, int]:
        calls["download"] += 1
        return b"", "text/plain", 200

    verified = discovery.verify_candidate(
        case,
        candidate,
        min_chars=5000,
        timeout=1,
        robots_checker=lambda url: False,
        downloader=downloader,
    )
    assert verified.verification_status == "robots_disallowed"
    assert verified.rejection_reason == "robots_txt_disallowed"
    assert calls["download"] == 0


def test_paywall_block_marker_is_rejected() -> None:
    case = discovery.TargetCase("NVDA_2026_Q4", "NVDA", "NVIDIA Corporation", "2026", "Q4", "nvidia.com")
    candidate = discovery.CandidateSource(source_url="https://investor.nvidia.com/transcript.txt")
    body = ("NVIDIA Q4 2026 earnings call Operator Question-and-Answer subscribe to continue " * 120).encode()
    verified = discovery.verify_candidate(
        case,
        candidate,
        min_chars=5000,
        timeout=1,
        robots_checker=lambda url: True,
        downloader=lambda url, timeout: (body, "text/plain", 200),
    )
    assert verified.verification_status == "paywalled"
    assert "paywall" in verified.rejection_reason
    assert verified.confidence < 0.70


def test_marker_detection_confidence_and_selection() -> None:
    case = discovery.TargetCase("NVDA_2026_Q4", "NVDA", "NVIDIA Corporation", "2026", "Q4", "nvidia.com")
    candidate = discovery.CandidateSource(source_url="https://investor.nvidia.com/NVDA_2026_Q4.txt")
    verified = discovery.verify_candidate(
        case,
        candidate,
        min_chars=5000,
        timeout=1,
        robots_checker=lambda url: True,
        downloader=lambda url, timeout: (LONG_TRANSCRIPT.encode(), "text/plain", 200),
    )
    assert verified.verification_status == "verified"
    assert {"operator", "question-and-answer", "prepared remarks", "analyst", "conference call", "earnings call"}.issubset(
        set(verified.matched_markers)
    )
    assert verified.confidence >= 0.70
    assert discovery.select_source([verified]) is verified


def test_short_candidate_does_not_meet_selected_threshold() -> None:
    short = discovery.CandidateSource(
        source_url="https://investor.nvidia.com/short.txt",
        confidence=0.95,
        verification_status="verified",
        transcript_char_estimate=200,
    )
    assert discovery.select_source([short]) is None


def test_output_csv_schema_and_intake_source_url_file_compatibility(tmp_path: Path) -> None:
    case = discovery.TargetCase("NVDA_2026_Q4", "NVDA", "NVIDIA Corporation", "2026", "Q4", "nvidia.com")
    candidate = discovery.CandidateSource(
        source_url="https://investor.nvidia.com/NVDA_2026_Q4.txt",
        source_type="txt",
        source_domain="investor.nvidia.com",
        confidence=0.80,
        verification_status="verified",
        transcript_char_estimate=6000,
        matched_markers=["operator", "question-and-answer"],
        notes="fixture",
    )
    discovery_case = discovery.CaseDiscovery(case=case, candidates=[candidate], selected_source_url=candidate.source_url)
    output = tmp_path / "source_urls.csv"
    discovery.write_source_csv(output, [discovery_case])
    with output.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == list(discovery.SOURCE_CSV_FIELDS)
        rows = list(reader)
    assert rows[0]["source_url"] == candidate.source_url
    loaded = intake.load_manual_source_urls(output)
    assert loaded["NVDA_2026_Q4"].source_url == candidate.source_url
    assert loaded["NVDA_2026_Q4"].quarter == "Q4"


def test_query_only_writes_queries_without_source_outputs(tmp_path: Path) -> None:
    output_csv = tmp_path / "source_urls.csv"
    candidates_json = tmp_path / "candidates.json"
    report_path = tmp_path / "report.md"
    queries_csv = tmp_path / "queries.csv"
    code = discovery.main(
        [
            "--tickers",
            "NVDA",
            "--years",
            "2026",
            "--quarters",
            "Q4",
            "--query-only",
            "--queries-csv",
            str(queries_csv),
            "--output-csv",
            str(output_csv),
            "--candidates-json",
            str(candidates_json),
            "--report-path",
            str(report_path),
        ]
    )
    assert code == 0
    assert queries_csv.exists()
    assert not output_csv.exists()
    assert not candidates_json.exists()
    assert not report_path.exists()
