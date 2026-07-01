from __future__ import annotations

from tools.download_first30_audio import _base_log


def test_audio_download_log_is_repo_safe() -> None:
    row = {"case_id": "vz_2024_q4", "ticker": "VZ", "audio_url": "https://www.verizon.com/audio.mp3"}
    log = _base_log(row)
    assert log["commit_allowed"] == "false"
    assert log["training_allowed"] == "false"
    assert log["raw_audio_committed"] == "false"
