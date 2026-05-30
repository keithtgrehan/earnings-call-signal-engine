from __future__ import annotations

from signal_engine.acquisition.direct_asset_detector import detect_direct_asset


def test_direct_asset_detector_confirms_transcript_markers() -> None:
    body = """
    Operator: Good morning and welcome to the Q4 earnings call.
    Corporate Participants
    Jane CEO
    Prepared Remarks
    Question-and-Answer
    Analyst: Can you discuss guidance?
    """

    result = detect_direct_asset(
        {
            "case_id": "jpm_2025_q4",
            "ticker": "JPM",
            "company_name": "JPMorgan Chase & Co.",
            "resolved_asset_url": "https://ir.example.com/q4-transcript.txt",
        },
        fetcher=lambda _url: (200, "text/plain", body.encode("utf-8")),
    )

    assert result["asset_type"] == "transcript_text"
    assert result["download_allowed"] == "true"
    assert result["blocked_reason"] == ""


def test_direct_asset_detector_confirms_audio_by_type_and_extension() -> None:
    result = detect_direct_asset(
        {"case_id": "jpm_2025_q4", "ticker": "JPM", "resolved_asset_url": "https://ir.example.com/q4-call.m4a"},
        fetcher=lambda _url: (200, "audio/mp4", b"\x00\x00audio"),
    )

    assert result["asset_type"] == "audio_m4a"
    assert result["download_allowed"] == "true"


def test_direct_asset_detector_blocks_youtube_signed_and_generic_html() -> None:
    youtube = detect_direct_asset({"resolved_asset_url": "https://youtube.com/watch?v=abc"}, fetcher=lambda _url: (200, "text/html", b""))
    signed = detect_direct_asset({"resolved_asset_url": "https://ir.example.com/q4.mp3?token=secret"}, fetcher=lambda _url: (200, "audio/mpeg", b""))
    generic = detect_direct_asset(
        {"resolved_asset_url": "https://ir.example.com/events"},
        fetcher=lambda _url: (200, "text/html", b"<html><body>Investor relations</body></html>"),
    )

    assert youtube["blocked_reason"] == "youtube_media_blocked"
    assert signed["blocked_reason"] == "signed_or_session_url_blocked"
    assert generic["blocked_reason"] == "generic_landing_page_no_direct_asset"


def test_direct_asset_detector_rejects_mismatched_official_ir_period_asset() -> None:
    result = detect_direct_asset(
        {
            "case_id": "c_2021_q4",
            "ticker": "C",
            "company_name": "Citigroup Inc.",
            "fiscal_period": "2021 Q4",
            "asset_type": "transcript_pdf",
            "source_type": "official_ir",
            "source_url": "https://www.citigroup.com/global/investors",
            "resolved_asset_url": "https://www.citigroup.com/storage/public/2026psqtr1-transcript.pdf",
            "download_allowed": "true",
        },
        fetcher=lambda _url: (200, "application/pdf", b"%PDF transcript"),
    )

    assert result["asset_type"] == "blocked"
    assert result["download_allowed"] == "false"
    assert result["blocked_reason"] == "mismatched_event_period_or_non_earnings"
