from __future__ import annotations

from signal_engine.media.event_windows import build_event_windows
from signal_engine.media.registration import build_media_registration, validate_media_registration


def test_manual_local_media_registration_blocks_commit_and_youtube() -> None:
    row = build_media_registration(
        media_path_ref="https://www.youtube.com/watch?v=demo",
        media_type="video",
        source_type="manual_local",
        rights_tier="publicly_available",
    )
    errors = validate_media_registration(row)
    assert "YouTube media download/registration as raw media is blocked" in errors
    assert "media_path_ref should be an absolute manual-local path" in errors


def test_media_event_windows_are_sparse_transcript_aligned() -> None:
    windows = build_event_windows([{"case_id": "case-1", "object_id": "obj-1", "span_hints": {"char_start": 1}}])
    assert windows[0]["media_scope"] == "sparse_transcript_aligned"
    assert windows[0]["full_call_processing_allowed"] is False
