from __future__ import annotations

from tools.check_local_asr_environment import check_local_asr_environment


def test_asr_environment_check_is_local_only(tmp_path) -> None:
    summary = check_local_asr_environment(workspace=tmp_path)
    assert summary["cloud_asr_used"] is False
    assert "ffmpeg" in summary
    assert "backends" in summary
