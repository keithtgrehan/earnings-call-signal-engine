from __future__ import annotations

from signal_engine.audio.windows import flagged_window_row


def test_flagged_audio_windows_are_review_windows_not_emotion_labels() -> None:
    row = flagged_window_row(case_id="case1", audio_sha256="sha256:" + "a" * 64, start_time_sec=1.0, end_time_sec=2.0, reason="qa_boundary")

    assert row["label_type"] == "review_window"
    assert row["emotion_label"] is False
    assert row["stress_label"] is False
    assert row["deception_label"] is False
