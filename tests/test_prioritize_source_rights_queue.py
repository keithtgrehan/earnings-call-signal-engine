from __future__ import annotations

from collections import Counter

from tools.prioritize_source_rights_queue import prioritize_rows


def test_prioritizes_official_transcripts_before_audio_and_blocks_youtube_media() -> None:
    rows = [
        {
            "case_id": "jpm_2025_q4",
            "ticker": "JPM",
            "company_name": "JPMorgan Chase",
            "fiscal_year": "2025",
            "fiscal_quarter": "Q4",
            "asset_type": "audio",
            "source_type": "official_ir_webcast",
            "source_url": "https://ir.example.com/audio.mp3",
            "source_domain": "ir.example.com",
            "rights_status": "metadata_only",
            "blocked_reason": "",
        },
        {
            "case_id": "jpm_2025_q4",
            "ticker": "JPM",
            "company_name": "JPMorgan Chase",
            "fiscal_year": "2025",
            "fiscal_quarter": "Q4",
            "asset_type": "transcript",
            "source_type": "company_ir",
            "source_url": "https://ir.example.com/transcript",
            "source_domain": "ir.example.com",
            "rights_status": "metadata_only",
            "blocked_reason": "",
        },
        {
            "case_id": "jpm_2025_q4",
            "ticker": "JPM",
            "asset_type": "audio",
            "source_type": "official_ir_webcast",
            "source_url": "https://youtube.com/watch?v=abc",
            "source_domain": "youtube.com",
            "rights_status": "metadata_only",
            "blocked_reason": "",
        },
    ]

    prioritized, exclusions = prioritize_rows(rows)

    assert prioritized[0]["asset_type"] == "transcript"
    assert prioritized[0]["source_type"] == "company_ir"
    assert exclusions == Counter({"exclude_youtube_media": 1})
