from __future__ import annotations

from pathlib import Path

from tools.validate_asr_segments import validate_segments


def test_validate_asr_segments_rejects_raw_text_commit(tmp_path: Path) -> None:
    path = tmp_path / "segments.csv"
    path.write_text(
        "segment_id,case_id,audio_asset_id,start_time_sec,end_time_sec,speaker,text_sha256,raw_text_committed\n"
        "seg1,vz_2024_q4,audio,0,1,,sha256:aaa,true\n",
        encoding="utf-8",
    )
    summary = validate_segments(path)
    assert summary["errors"]
