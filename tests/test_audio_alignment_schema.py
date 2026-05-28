from __future__ import annotations

from signal_engine.audio.alignment import alignment_row


def test_alignment_row_is_metadata_only() -> None:
    row = alignment_row(case_id="case1", audio_sha256="sha256:" + "a" * 64, transcript_sha256="sha256:" + "b" * 64)

    assert row["alignment_status"] == "not_run"
    assert row["raw_text_committed"] is False
