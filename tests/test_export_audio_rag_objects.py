from __future__ import annotations

from pathlib import Path

from tools.export_audio_rag_objects import export_audio_objects


def test_audio_objects_require_aligned_manifest(tmp_path: Path) -> None:
    audio = tmp_path / "audio.csv"
    align = tmp_path / "align.csv"
    out = tmp_path / "out.csv"
    audio.write_text("case_id,audio_asset_id,sha256,rights_status\nvz_2024_q4,audio,sha256:aaa,safe_to_download\n", encoding="utf-8")
    align.write_text("alignment_id,case_id,audio_asset_id,alignment_status\nal1,vz_2024_q4,audio,not_run\n", encoding="utf-8")
    summary = export_audio_objects(audio_registry=audio, alignment_manifest=align, out_path=out)
    assert summary["audio_objects"] == 0
