from __future__ import annotations

from tools.resolve_first30_missing_transcript_urls import generated_candidate_urls, score_transcript_replacement


def test_jpm_q1_known_official_replacement_scores_high() -> None:
    row = {
        "case_id": "jpm_2025_q1",
        "ticker": "JPM",
        "fiscal_year": "2025",
        "fiscal_quarter": "Q1",
        "source_url": "https://www.jpmorganchase.com/ir",
        "source_type": "official_ir",
        "expected_format": "pdf",
        "exchange": "NYSE",
        "commit_allowed": "false",
        "training_allowed": "false",
    }
    urls = generated_candidate_urls(row)
    assert urls and urls[0].endswith("1q25-earnings-transcript.pdf")
    confidence, reason, blocker = score_transcript_replacement(row, urls[0], accessible=True)
    assert confidence >= 0.75
    assert blocker == ""
    assert "fiscal_period_url_match" in reason


def test_transcript_resolver_blocks_youtube_and_unverified_period() -> None:
    row = {
        "case_id": "jpm_2025_q4",
        "ticker": "JPM",
        "fiscal_year": "2025",
        "fiscal_quarter": "Q4",
        "source_url": "https://www.jpmorganchase.com/ir",
        "source_type": "official_ir",
        "expected_format": "pdf",
        "exchange": "NYSE",
        "commit_allowed": "false",
        "training_allowed": "false",
    }
    _, _, blocker = score_transcript_replacement(row, "https://youtube.com/watch?v=abc", accessible=True)
    assert blocker == "youtube_media_requires_written_authorization"
    _, _, blocker = score_transcript_replacement(
        row,
        "https://www.jpmorganchase.com/content/dam/jpmc/example/1q25-earnings-transcript.pdf",
        accessible=True,
    )
    assert blocker == "fiscal_period_not_verified"
