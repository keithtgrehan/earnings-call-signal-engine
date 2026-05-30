from __future__ import annotations

from pathlib import Path


def test_no_raw_audio_media_committed() -> None:
    blocked = {".mp3", ".m4a", ".wav", ".mp4", ".mov"}
    offenders = [path for path in Path(".").rglob("*") if ".git" not in path.parts and path.suffix.lower() in blocked]
    assert offenders == []
