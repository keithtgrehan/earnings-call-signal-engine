from __future__ import annotations

from pathlib import Path

from scripts.validate_first30_ingestion_manifest import validate_manifest
from tools.first30_transcript_common import build_promotion_rows, read_csv


def test_promotion_keeps_raw_and_training_disallowed() -> None:
    rows = build_promotion_rows(read_csv(Path("data/acquisition/transcript_candidates_first30.csv")))
    assert rows
    assert all(row["commit_allowed"] == "false" for row in rows)
    assert all(row["training_allowed"] == "false" for row in rows)
    assert all(row["raw_text_committed"] == "false" for row in rows)


def test_vz_2024_q4_is_first_download_priority() -> None:
    rows = build_promotion_rows(read_csv(Path("data/acquisition/transcript_candidates_first30.csv")))
    vz = next(row for row in rows if row["case_id"] == "vz_2024_q4")
    assert vz["priority_rank"] == "1"
    assert vz["download_allowed"] == "true"
    assert vz["commit_allowed"] == "false"


def test_manifest_validator_accepts_generated_shape(tmp_path: Path) -> None:
    rows = build_promotion_rows(read_csv(Path("data/acquisition/transcript_candidates_first30.csv")))
    path = tmp_path / "manifest.csv"
    from tools.first30_transcript_common import FIRST30_INGESTION_FIELDS, write_csv

    write_csv(path, rows, FIRST30_INGESTION_FIELDS)
    summary = validate_manifest(path)
    assert summary["errors"] == []
