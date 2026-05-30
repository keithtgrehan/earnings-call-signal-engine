from __future__ import annotations

from pathlib import Path

from tools.probe_audio_asset import probe_audio


def test_probe_audio_missing_file_is_metadata_status() -> None:
    result = probe_audio(Path("/tmp/signal-engine-missing-audio.mp3"))
    assert result["ffprobe_status"] == "missing_file"
