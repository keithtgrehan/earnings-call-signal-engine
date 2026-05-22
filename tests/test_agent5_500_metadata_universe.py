from __future__ import annotations

from signal_engine.agent5_acquisition import build_500_call_metadata_universe


def test_500_call_metadata_universe_is_target_slots_only() -> None:
    rows = build_500_call_metadata_universe(count=500)
    assert len(rows) == 500
    assert all(row["exchange"] == "NYSE" for row in rows)
    assert all(row["raw_transcript_allowed"] is False for row in rows)
    assert all(row["raw_audio_allowed"] is False for row in rows)
    assert all(row["raw_video_allowed"] is False for row in rows)
    assert all("metadata_only" in row["quality_flags"] for row in rows)
