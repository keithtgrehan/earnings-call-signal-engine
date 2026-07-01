from __future__ import annotations

from signal_engine.acquisition.asset_resolver import resolve_official_ir_event_rows


def test_event_resolver_prioritizes_period_matched_event_page_assets() -> None:
    pages = {
        "https://ir.example.com": (
            200,
            "text/html",
            '<a href="/events-and-presentations">Events and presentations</a>',
        ),
        "https://ir.example.com/events-and-presentations": (
            200,
            "text/html",
            """
            <a href="/events/q3-2025-earnings-call">Q3 2025 earnings call webcast</a>
            <a href="/events/q2-2025-earnings-call">Q2 2025 earnings call webcast</a>
            """,
        ),
        "https://ir.example.com/events/q3-2025-earnings-call": (
            200,
            "text/html",
            """
            <a href="/files/q3-2025-earnings-transcript.pdf">Q3 2025 earnings call transcript</a>
            <script>var replay = "https://ir.example.com/media/q3-2025-earnings-call.mp3";</script>
            """,
        ),
        "https://ir.example.com/events/q2-2025-earnings-call": (
            200,
            "text/html",
            '<a href="/files/q2-2025-earnings-transcript.pdf">Q2 2025 earnings transcript</a>',
        ),
    }

    def fetcher(url: str) -> tuple[int, str, str]:
        return pages[url]

    rows = [
        {
            "case_id": "jpm_2025_q3",
            "ticker": "JPM",
            "company_name": "JPMorgan Chase & Co.",
            "fiscal_year": "2025",
            "fiscal_quarter": "Q3",
            "source_url": "https://ir.example.com",
            "source_type": "official_ir",
        }
    ]

    candidates = resolve_official_ir_event_rows(rows, fetcher=fetcher, robots_allowed=lambda _url: True)
    permitted = {row["resolved_asset_url"]: row for row in candidates if row["download_allowed"] == "true"}

    assert "https://ir.example.com/files/q3-2025-earnings-transcript.pdf" in permitted
    assert "https://ir.example.com/media/q3-2025-earnings-call.mp3" in permitted
    assert "https://ir.example.com/files/q2-2025-earnings-transcript.pdf" not in permitted
    assert permitted["https://ir.example.com/files/q3-2025-earnings-transcript.pdf"]["asset_type"] == "transcript_pdf"
    assert permitted["https://ir.example.com/media/q3-2025-earnings-call.mp3"]["asset_type"] == "audio_mp3"
