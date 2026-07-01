from __future__ import annotations

import csv
from pathlib import Path


MANIFEST = Path("data/acquisition/first30_audio_source_gap_manifest.csv")


def _rows() -> list[dict[str, str]]:
    with MANIFEST.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def test_audio_source_gap_manifest_blocks_player_downloads() -> None:
    rows = _rows()
    assert rows
    for row in rows:
        assert row["commit_allowed"] == "false"
        assert row["training_allowed"] == "false"
        assert row["raw_audio_committed"] == "false"
    player_rows = [row for row in rows if row["source_type"] == "webcast_player_only"]
    assert len(player_rows) == 5
    assert all(row["download_allowed"] == "false" for row in player_rows)
    assert all(row["source_status"] == "metadata_only" for row in player_rows)


def test_vz_prepared_audio_is_support_only() -> None:
    vz = next(row for row in _rows() if row["case_id"] == "vz_2024_q4")
    assert vz["source_type"] == "official_ir_direct_audio"
    assert vz["source_status"] == "prepared_only"
    assert vz["usage_scope"] == "support_only"
    assert vz["download_allowed"] == "false"
    assert "full-call" in vz["notes"]
