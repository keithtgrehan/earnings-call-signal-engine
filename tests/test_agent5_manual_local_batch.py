from __future__ import annotations

from pathlib import Path

from signal_engine.agent5_acquisition import build_manual_local_registry, validate_manual_local_registry


def test_manual_local_batch_records_path_and_hash_only(tmp_path: Path) -> None:
    transcript = tmp_path / "local_transcript.txt"
    transcript.write_text("Management: We raised revenue guidance for FY2024.\n", encoding="utf-8")
    rows = build_manual_local_registry(
        [
            {
                "case_id": "case_local_001",
                "ticker": "JPM",
                "source_path_ref": str(transcript),
                "media_type": "transcript",
                "rights_tier": "manual_supplied",
            }
        ]
    )
    assert not validate_manual_local_registry(rows)
    record = rows[0]
    assert record["source_path_ref"] == str(transcript)
    assert str(record["source_sha256"]).startswith("sha256:")
    assert record["raw_file_copied_into_repo"] is False
    assert "raised revenue guidance" not in str(record)


def test_unknown_manual_local_rights_block_commit_training_eval(tmp_path: Path) -> None:
    transcript = tmp_path / "local_transcript.txt"
    transcript.write_text("Analyst: Why is demand weak?\n", encoding="utf-8")
    rows = build_manual_local_registry(
        [
            {
                "case_id": "case_local_002",
                "source_path_ref": str(transcript),
                "media_type": "transcript",
                "rights_tier": "unknown",
                "commit_allowed": True,
            }
        ]
    )
    assert any("unknown/restricted manual-local rights" in error for error in validate_manual_local_registry(rows))
