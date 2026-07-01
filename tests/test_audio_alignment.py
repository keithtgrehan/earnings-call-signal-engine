from __future__ import annotations

from signal_engine.audio.alignment import alignment_row, fuzzy_window_score, prepared_section, token_overlap_score


def test_alignment_row_is_metadata_only() -> None:
    row = alignment_row(case_id="vz_2024_q4", audio_sha256="sha256:" + "a" * 64, transcript_sha256="sha256:" + "b" * 64)
    assert row["alignment_status"] == "not_run"
    assert row["raw_text_committed"] is False
    assert row["matched_span_count"] == 0


def test_token_overlap_scores_shared_words() -> None:
    score = token_overlap_score("prepared remarks revenue margin", "revenue and margin prepared remarks")
    assert score > 0.5


def test_prepared_section_stops_before_qna() -> None:
    text = "Prepared remarks here\nQuestion-and-Answer Session\nAnalyst question"
    prepared, start, end = prepared_section(text)
    assert start == 0
    assert end < len(text)
    assert "Analyst question" not in prepared


def test_fuzzy_window_finds_anchor() -> None:
    transcript = "intro " * 100 + "we reported revenue growth and margin expansion in prepared remarks " + "tail " * 100
    result = fuzzy_window_score("revenue growth margin expansion prepared remarks", transcript, window_chars=200, stride_chars=50)
    assert result["score"] > 0.05
