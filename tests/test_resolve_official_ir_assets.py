from __future__ import annotations

from signal_engine.acquisition.asset_resolver import (
    RESOLVED_ASSET_FIELDS,
    rank_asset_type,
    resolve_official_ir_rows,
)


def test_official_ir_resolver_extracts_direct_assets_and_landing_page() -> None:
    html = """
    <html><head>
      <link rel="canonical" href="https://ir.example.com/events/q4-2025">
      <meta property="og:url" content="https://ir.example.com/events/q4-2025">
      <script type="application/ld+json">{"url": "https://ir.example.com/files/q4-transcript.txt"}</script>
    </head><body>
      <a href="/files/q4-transcript.pdf">Q4 earnings call transcript PDF</a>
      <a href="/media/q4-call.mp3">Q4 earnings call replay audio</a>
      <a href="/files/q4-results-slides.pdf">Q4 presentation slides</a>
      <a href="https://www.youtube.com/watch?v=blocked">YouTube replay</a>
    </body></html>
    """

    def fetcher(url: str) -> tuple[int, str, str]:
        assert url == "https://ir.example.com/events"
        return 200, "text/html", html

    rows = [
        {
            "case_id": "jpm_2025_q4",
            "ticker": "JPM",
            "company_name": "JPMorgan Chase & Co.",
            "fiscal_year": "2025",
            "fiscal_quarter": "Q4",
            "event_date": "2025-12-31",
            "source_url": "https://ir.example.com/events",
            "source_type": "official_ir",
            "approval_ref": "approval://project-assessment",
        }
    ]

    candidates = resolve_official_ir_rows(rows, fetcher=fetcher, robots_allowed=lambda _url: True)

    assert RESOLVED_ASSET_FIELDS[0] == "candidate_id"
    asset_types = {row["asset_type"] for row in candidates}
    assert {"landing_page", "transcript_pdf", "transcript_text", "audio_mp3", "slides_metadata", "blocked"}.issubset(asset_types)
    transcript = next(row for row in candidates if row["asset_type"] == "transcript_pdf")
    assert transcript["download_allowed"] == "true"
    assert transcript["rights_status"] == "user_authorized_public_direct"
    assert transcript["blocked_reason"] == ""
    youtube = next(row for row in candidates if "youtube.com" in row["resolved_asset_url"])
    assert youtube["asset_type"] == "blocked"
    assert youtube["blocked_reason"] == "youtube_media_blocked"


def test_official_ir_resolver_records_robots_block_as_blocked_candidate() -> None:
    rows = [
        {
            "case_id": "jpm_2025_q4",
            "ticker": "JPM",
            "company_name": "JPMorgan Chase & Co.",
            "fiscal_year": "2025",
            "fiscal_quarter": "Q4",
            "event_date": "2025-12-31",
            "source_url": "https://ir.example.com/events",
            "source_type": "official_ir",
        }
    ]

    candidates = resolve_official_ir_rows(rows, fetcher=lambda _url: (200, "text/html", ""), robots_allowed=lambda _url: False)

    assert len(candidates) == 1
    assert candidates[0]["asset_type"] == "blocked"
    assert candidates[0]["blocked_reason"] == "robots_or_source_terms_hard_block"
    assert candidates[0]["download_allowed"] == "false"


def test_asset_ranking_prefers_direct_transcript_then_audio_then_metadata() -> None:
    assert rank_asset_type("transcript_text") < rank_asset_type("audio_mp3") < rank_asset_type("sec_exhibit") < rank_asset_type("blocked")


def test_official_ir_resolver_does_not_permit_mismatched_period_transcripts() -> None:
    html = """
    <a href="/documents/quarterly-earnings/2026/1st-quarter/1q26-earnings-transcript.pdf">1Q26 earnings transcript</a>
    <a href="/documents/quarterly-earnings/2025/4th-quarter/4q25-earnings-transcript.pdf">4Q25 earnings transcript</a>
    <a href="/documents/events/2025/investor-day/full-transcript.pdf">Investor day transcript</a>
    """
    rows = [
        {
            "case_id": "jpm_2025_q4",
            "ticker": "JPM",
            "company_name": "JPMorgan Chase & Co.",
            "fiscal_year": "2025",
            "fiscal_quarter": "Q4",
            "source_url": "https://ir.example.com/events",
            "source_type": "official_ir",
        }
    ]

    candidates = resolve_official_ir_rows(rows, fetcher=lambda _url: (200, "text/html", html), robots_allowed=lambda _url: True)
    permitted_urls = {row["resolved_asset_url"] for row in candidates if row["download_allowed"] == "true"}

    assert "https://ir.example.com/documents/quarterly-earnings/2025/4th-quarter/4q25-earnings-transcript.pdf" in permitted_urls
    assert "https://ir.example.com/documents/quarterly-earnings/2026/1st-quarter/1q26-earnings-transcript.pdf" not in permitted_urls
    assert "https://ir.example.com/documents/events/2025/investor-day/full-transcript.pdf" not in permitted_urls
