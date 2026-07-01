from __future__ import annotations

import subprocess
from pathlib import Path


def test_no_raw_audio_media_committed() -> None:
    blocked = {".mp3", ".m4a", ".wav", ".mp4", ".mov"}
    tracked = subprocess.run(["git", "ls-files"], text=True, capture_output=True, check=True).stdout.splitlines()
    offenders = [Path(path) for path in tracked if Path(path).suffix.lower() in blocked]
    assert offenders == []
