from __future__ import annotations

from pathlib import Path

from tools.run_local_asr_smoke import run_local_asr_smoke


def test_asr_smoke_handles_missing_audio_registry(tmp_path: Path) -> None:
    summary = run_local_asr_smoke(
        audio_registry=tmp_path / "missing_audio.csv",
        workspace=tmp_path,
        out_manifest=tmp_path / "asr.csv",
        segment_manifest=tmp_path / "segments.csv",
    )
    assert summary["status"] == "no_registered_audio"
    assert summary["cloud_asr_used"] is False
    assert (tmp_path / "asr.csv").exists()
