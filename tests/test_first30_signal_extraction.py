from __future__ import annotations

from pathlib import Path

from signal_engine.first30_extraction import extract_candidates_from_retrieval_objects


def _retrieval_row(chunk_path: Path) -> dict[str, str]:
    return {
        "object_id": "obj1",
        "object_type": "evidence_object",
        "case_id": "jpm_2025_q4",
        "ticker": "JPM",
        "fiscal_period": "2025 Q4",
        "source_ref": str(chunk_path),
        "source_sha256": "sha256:" + "a" * 64,
        "text_sha256": "sha256:" + "b" * 64,
        "normalized_transcript_sha256": "sha256:" + "c" * 64,
        "provenance_hash": "sha256:" + "d" * 64,
        "topic": "guidance_statement",
        "section": "prepared_remarks",
        "speaker": "management",
        "span_start_char": "10",
        "span_end_char": "100",
        "raw_text_committed": "false",
    }


def test_first30_signal_extraction_generates_not_gold_metadata_only_candidates(tmp_path: Path) -> None:
    chunk = tmp_path / "chunk.txt"
    chunk.write_text("Management raised guidance and updated the outlook for the year.", encoding="utf-8")

    rows, summary = extract_candidates_from_retrieval_objects([_retrieval_row(chunk)])

    assert summary["candidate_count"] == 1
    assert rows[0]["label"] == "guidance_revision"
    assert rows[0]["gold_status"] == "not_gold"
    assert rows[0]["review_status"] == "pending_human_review"
    assert rows[0]["raw_text_committed"] == "false"
    assert "raised guidance" not in str(rows[0]).lower()
