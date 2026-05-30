from __future__ import annotations

from pathlib import Path

from signal_engine.first30_extraction import expand_first100_candidates_from_retrieval_objects


def _row(chunk_path: Path, object_id: str, object_type: str = "evidence_object") -> dict[str, str]:
    return {
        "object_id": object_id,
        "object_type": object_type,
        "case_id": "jpm_2025_q4",
        "ticker": "JPM",
        "fiscal_period": "2025 Q4",
        "source_ref": str(chunk_path),
        "source_sha256": "sha256:" + "a" * 64,
        "text_sha256": "sha256:" + "b" * 64,
        "normalized_transcript_sha256": "sha256:" + "c" * 64,
        "provenance_hash": "sha256:" + "d" * 64,
        "topic": "prepared_remarks",
        "section": "prepared_remarks",
        "speaker": "management",
        "span_start_char": "1",
        "span_end_char": "100",
        "raw_text_committed": "false",
    }


def test_first100_expansion_generates_metadata_only_candidates(tmp_path: Path) -> None:
    evidence = tmp_path / "chunk_evidence.txt"
    evidence.write_text("Management raised guidance and updated the outlook.", encoding="utf-8")
    semantic = tmp_path / "chunk_semantic.txt"
    semantic.write_text("Background discussion with no review signal.", encoding="utf-8")

    rows, summary, suppressions = expand_first100_candidates_from_retrieval_objects(
        [_row(evidence, "evidence_1"), _row(semantic, "semantic_1", "semantic_chunk")],
        target_count=2,
    )

    assert summary["candidate_count"] == 2
    assert rows[0]["suggested_label"] == "guidance_revision"
    assert rows[1]["suggested_label"] == "neutral/no_signal"
    assert rows[0]["gold_status"] == "not_gold"
    assert rows[0]["review_status"] == "pending_human_review"
    assert rows[0]["raw_text_committed"] == "false"
    assert "raised guidance" not in str(rows).lower()
    assert suppressions == []


def test_first100_expansion_suppresses_safe_harbor(tmp_path: Path) -> None:
    chunk = tmp_path / "safe_harbor.txt"
    chunk.write_text("Forward-looking statements and safe harbor language.", encoding="utf-8")

    rows, summary, suppressions = expand_first100_candidates_from_retrieval_objects([_row(chunk, "evidence_1")])

    assert rows == []
    assert summary["suppressed"]["safe_harbor"] == 1
    assert suppressions[0]["reason"] == "safe_harbor"
