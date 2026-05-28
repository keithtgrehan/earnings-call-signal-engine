from __future__ import annotations

from tools.discover_company_ir_sources import extract_candidate_links
from signal_engine.acquisition.source_adapters import (
    SOURCE_CANDIDATE_FIELDS,
    SourceCandidate,
    candidate_to_csv_row,
    normalize_candidate,
    validate_candidate,
)


def test_candidate_defaults_are_fail_closed() -> None:
    candidate = normalize_candidate(
        {
            "case_id": "jpm_2025_q1",
            "ticker": "JPM",
            "company_name": "JPMorgan Chase & Co.",
            "source_url": "https://ir.example.com/events",
            "source_type": "company_ir",
        }
    )

    assert candidate.rights_status == "unknown_fail_closed"
    assert candidate.download_allowed is False
    assert candidate.approval_required is True
    assert candidate.raw_text_committed is False
    assert validate_candidate(candidate) == []


def test_unknown_rights_cannot_enable_download() -> None:
    candidate = normalize_candidate(
        {
            "case_id": "jpm_2025_q1",
            "ticker": "JPM",
            "source_url": "https://ir.example.com/events",
            "rights_status": "unknown",
            "download_allowed": "true",
        }
    )

    assert candidate.rights_status == "unknown_fail_closed"
    assert candidate.download_allowed is False


def test_input_cannot_disable_manual_approval_requirement() -> None:
    candidate = normalize_candidate(
        {
            "source_url": "https://ir.example.com/events",
            "approval_required": "false",
            "rights_status": "metadata_only",
        }
    )

    assert candidate.approval_required is True


def test_paid_candidate_without_license_is_invalid_for_raw_access() -> None:
    candidate = SourceCandidate(
        candidate_id="cand_paid",
        case_id="jpm_2025_q1",
        ticker="JPM",
        company_name="JPMorgan Chase & Co.",
        fiscal_period="FY2025 Q1",
        event_date="2025-04-14",
        source_type="paid_transcript_api",
        source_name="Fixture API",
        source_domain="api.example.com",
        source_url="https://api.example.com/transcripts/JPM",
        discovered_from_url="",
        discovery_method="paid_api_metadata_scaffold",
        candidate_kind="transcript",
        rights_status="licensed_vendor_metadata_only",
        download_allowed=True,
        approval_required=True,
        raw_text_committed=False,
        license_config_ref="",
        robots_allowed=False,
        paywall_status="api_key_required",
        confidence=0.5,
        notes="metadata only",
    )

    assert any("license_config_ref" in error for error in validate_candidate(candidate))


def test_candidate_to_csv_row_preserves_field_order() -> None:
    row = candidate_to_csv_row(normalize_candidate({"source_url": "https://ir.example.com/events"}))

    assert list(row.keys()) == SOURCE_CANDIDATE_FIELDS


def test_local_html_link_extraction_classifies_ir_links_without_network() -> None:
    html = """
    <html>
      <body>
        <a href="/investor-relations">Investor relations</a>
        <a href="/events/q1-transcript">Q1 transcript</a>
        <a href="/events/q1-webcast">Webcast replay</a>
        <a href="/presentations/q1-slides.pdf">Presentation</a>
        <a href="https://youtube.com/watch?v=abc">Video replay</a>
      </body>
    </html>
    """

    links = extract_candidate_links("https://ir.example.com/events", html)
    by_url = {row["source_url"]: row["candidate_kind"] for row in links}

    assert by_url["https://ir.example.com/investor-relations"] == "company_ir"
    assert by_url["https://ir.example.com/events/q1-transcript"] == "transcript"
    assert by_url["https://ir.example.com/events/q1-webcast"] == "webcast"
    assert by_url["https://ir.example.com/presentations/q1-slides.pdf"] == "presentation"
    assert by_url["https://youtube.com/watch?v=abc"] == "youtube_or_external_video"


def test_youtube_media_links_remain_metadata_only_and_non_downloadable() -> None:
    candidate = normalize_candidate(
        {
            "source_url": "https://www.youtube.com/watch?v=abc",
            "source_type": "company_ir",
            "candidate_kind": "youtube_or_external_video",
            "rights_status": "metadata_only",
            "download_allowed": "true",
        }
    )

    assert candidate.rights_status == "metadata_only"
    assert candidate.download_allowed is False
    assert candidate.raw_text_committed is False
