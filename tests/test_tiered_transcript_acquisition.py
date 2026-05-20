from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import acquire_verified_transcripts as acquire  # noqa: E402
import discover_transcript_sources as discover  # noqa: E402


LONG_TRANSCRIPT = (
    "NVIDIA Corporation Q1 2026 earnings call transcript\n"
    "Operator: Welcome to the earnings call.\n"
    "Prepared remarks\n"
    "CEO: NVIDIA delivered strong Q1 FY2026 results and demand commentary.\n"
    "Question-and-Answer\n"
    "Analyst: Can you discuss Q1 2026 demand and guidance?\n"
    + " ".join(f"NVIDIA Q1 2026 conference call prepared remarks analyst answer {index}." for index in range(280))
)


def target() -> discover.TieredTarget:
    return discover.TieredTarget("1", "NVDA_2026_Q1", "NVDA", "NVIDIA Corporation", "2026", "Q1", "P1", "fixture")


def candidate(url: str = "https://investor.nvidia.com/NVDA_2026_Q1.txt") -> discover.CandidateURL:
    return discover.CandidateURL(target=target(), source_url=url, discovery_method="fixture")


def test_tier_target_config_parsing(tmp_path: Path) -> None:
    path = tmp_path / "targets.csv"
    path.write_text(
        "tier,case_id,ticker,company_name,fiscal_year,quarter,priority,notes\n"
        "1,NVDA_2026_Q1,NVDA,NVIDIA Corporation,2026,Q1,P1,fixture\n",
        encoding="utf-8",
    )
    targets = discover.read_targets(path)
    assert targets == [target()]


def test_quality_score_generation_and_repeatability() -> None:
    first = discover.score_acquisition_quality(
        target=target(),
        text=LONG_TRANSCRIPT,
        source_url="https://investor.nvidia.com/NVDA_2026_Q1.txt",
        source_type="txt",
        content_type="text/plain",
        verification_status="candidate",
        min_chars=500,
    )
    second = discover.score_acquisition_quality(
        target=target(),
        text=LONG_TRANSCRIPT,
        source_url="https://investor.nvidia.com/NVDA_2026_Q1.txt",
        source_type="txt",
        content_type="text/plain",
        verification_status="candidate",
        min_chars=500,
    )
    assert first.score == second.score
    assert first.band == "high"


def test_quality_band_thresholds_and_hard_failures() -> None:
    assert discover.band_for_score(85) == "high"
    assert discover.band_for_score(60) == "medium"
    assert discover.band_for_score(40) == "low"
    assert discover.band_for_score(39) == "unusable"
    assert discover.band_for_score(90, hard_fail=True) == "unusable"


def test_robots_disallowed_rejects_without_fetching() -> None:
    calls = {"metadata": 0, "content": 0}

    def metadata_fetcher(url: str, timeout: int) -> discover.FetchMetadata:
        calls["metadata"] += 1
        return discover.FetchMetadata(200, "text/plain")

    def content_fetcher(url: str, timeout: int) -> tuple[bytes, str, int]:
        calls["content"] += 1
        return LONG_TRANSCRIPT.encode(), "text/plain", 200

    result = discover.verify_candidate(
        candidate(),
        min_chars=500,
        timeout=1,
        robots_checker=lambda url: False,
        metadata_fetcher=metadata_fetcher,
        content_fetcher=content_fetcher,
    )
    assert result.verification_status == "robots_disallowed"
    assert result.acquisition_quality_band == "unusable"
    assert calls == {"metadata": 0, "content": 0}


def test_paywall_marker_forces_unusable() -> None:
    body = (LONG_TRANSCRIPT + " subscribe to continue").encode()
    result = discover.verify_candidate(
        candidate(),
        min_chars=500,
        timeout=1,
        robots_checker=lambda url: True,
        metadata_fetcher=lambda url, timeout: discover.FetchMetadata(200, "text/plain"),
        content_fetcher=lambda url, timeout: (body, "text/plain", 200),
    )
    assert result.verification_status == "paywalled"
    assert result.acquisition_quality_score == 0
    assert result.acquisition_quality_band == "unusable"


def test_pdf_queue_generation_and_pdf_excluded_from_acquisition(tmp_path: Path) -> None:
    result = discover.verify_candidate(
        candidate("https://investor.nvidia.com/NVDA_2026_Q1.pdf"),
        min_chars=500,
        timeout=1,
        robots_checker=lambda url: True,
        metadata_fetcher=lambda url, timeout: discover.FetchMetadata(200, "application/pdf"),
        content_fetcher=lambda url, timeout: (_ for _ in ()).throw(AssertionError("PDF content must not be fetched")),
    )
    row = discover.result_to_row(result)
    acquisition = acquire.acquire_row(
        {key: str(value) for key, value in row.items()},
        manual_source_root=tmp_path / "manual_sources",
        timeout=1,
        overwrite=False,
        robots_checker=lambda url: True,
        text_fetcher=lambda url, timeout: (_ for _ in ()).throw(AssertionError("PDF must not be acquired")),
    )
    pdf_row = acquire.pdf_queue_row({key: str(value) for key, value in row.items()})
    assert result.verification_status == "verified_manual_pdf"
    assert result.verified_allowed is False
    assert acquisition.status == "pdf_manual_conversion_required"
    assert pdf_row["verification_status"] == "verified_manual_pdf"
    assert pdf_row["manual_conversion_status"] == "pending_manual_conversion"


def test_plaintext_normalization_and_no_overwrite(tmp_path: Path) -> None:
    row = {
        "case_id": "NVDA_2026_Q1",
        "ticker": "NVDA",
        "company_name": "NVIDIA Corporation",
        "fiscal_year": "2026",
        "quarter": "Q1",
        "source_url": "https://investor.nvidia.com/NVDA_2026_Q1.txt",
        "source_type": "txt",
        "estimated_pdf": "false",
        "verified_allowed": "true",
        "matched_markers": "operator;prepared remarks;question-and-answer",
        "acquisition_quality_band": "high",
        "discovery_method": "fixture",
    }
    root = tmp_path / "manual_sources"
    first = acquire.acquire_row(
        row,
        manual_source_root=root,
        timeout=1,
        overwrite=False,
        robots_checker=lambda url: True,
        text_fetcher=lambda url, timeout: ("NVIDIA\r\nQ1 2026\r\n" + LONG_TRANSCRIPT, "txt"),
    )
    second = acquire.acquire_row(
        row,
        manual_source_root=root,
        timeout=1,
        overwrite=False,
        robots_checker=lambda url: True,
        text_fetcher=lambda url, timeout: ("replacement", "txt"),
    )
    raw_path = Path(first.local_file_path)
    assert first.status == "acquired"
    assert "NVIDIA Q1 2026" in raw_path.read_text(encoding="utf-8")
    assert second.status == "skipped_existing_raw"


def test_manual_fallback_report_includes_pdf_and_blocked_sections(tmp_path: Path) -> None:
    pdf = acquire.AcquisitionResult(row={"case_id": "NVDA_2026_Q1", "source_url": "https://example.com/a.pdf", "estimated_pdf": "true"}, status="pdf_manual_conversion_required")
    blocked = acquire.AcquisitionResult(row={"case_id": "MSFT_2026_Q1", "source_url": "https://example.com/b", "estimated_pdf": "false"}, status="fallback_required", rejection_reason="robots_txt_disallowed")
    report = tmp_path / "acquisition.md"
    fallback = tmp_path / "fallback.md"
    acquire.write_reports(report, fallback, [pdf, blocked], [acquire.pdf_queue_row(pdf.row)])
    text = fallback.read_text(encoding="utf-8")
    assert "PDF Manual Conversion Queue" in text
    assert "Blocked Or Unusable Candidates" in text
    assert "robots_txt_disallowed" in text


def test_staged_transcript_guard_matches_forbidden_paths() -> None:
    from check_no_transcript_text_staged import is_forbidden_transcript_artifact  # noqa: PLC0415

    assert is_forbidden_transcript_artifact("data/corpus/high_signal_cases/NVDA/raw/transcript.txt")
    assert is_forbidden_transcript_artifact("data/corpus/high_signal_cases/NVDA/processed/transcript_clean.txt")
    assert is_forbidden_transcript_artifact("data/corpus/high_signal_cases/NVDA/labels/human_labeling_packet.md")
    assert not is_forbidden_transcript_artifact("data/corpus/discovered_transcript_sources.csv")


def test_discovered_csv_includes_quality_fields(tmp_path: Path) -> None:
    result = discover.verify_candidate(
        candidate(),
        min_chars=500,
        timeout=1,
        robots_checker=lambda url: True,
        metadata_fetcher=lambda url, timeout: discover.FetchMetadata(200, "text/plain"),
        content_fetcher=lambda url, timeout: (LONG_TRANSCRIPT.encode(), "text/plain", 200),
    )
    output = tmp_path / "discovered.csv"
    discover.write_discovered_csv(output, [result])
    rows = list(csv.DictReader(output.open(encoding="utf-8")))
    assert rows[0]["acquisition_quality_score"]
    assert rows[0]["acquisition_quality_band"] == "high"
