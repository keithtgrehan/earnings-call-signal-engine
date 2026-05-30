from __future__ import annotations

from signal_engine.first30_extraction import FIRST100_CANDIDATE_FIELDS, validate_first100_candidate_rows


def _candidate() -> dict[str, str]:
    row = {field: "" for field in FIRST100_CANDIDATE_FIELDS}
    row.update(
        {
            "candidate_id": "cand1",
            "case_id": "hd_2025_q4",
            "ticker": "HD",
            "fiscal_period": "2025 Q4",
            "suggested_label": "uncertainty",
            "suggested_confidence": "0.64",
            "evidence_object_id": "evidence1",
            "chunk_id": "chunk1",
            "retrieval_object_id": "object1",
            "object_type": "evidence_object",
            "source_path": "/Users/keith/Desktop/earnings calls 100 samples/HD/chunk.txt",
            "source_sha256": "sha256:" + "a" * 64,
            "normalized_transcript_hash": "sha256:" + "b" * 64,
            "text_hash": "sha256:" + "c" * 64,
            "provenance_hash": "sha256:" + "d" * 64,
            "speaker_role": "management",
            "transcript_section": "prepared_remarks",
            "rule_id": "uncertainty_terms",
            "rule_version": "first100_deterministic_v1",
            "contamination_flags": "machine_candidate_only;not_gold",
            "gold_status": "not_gold",
            "review_status": "pending_human_review",
            "raw_text_committed": "false",
            "commit_allowed": "false",
            "training_allowed": "false",
        }
    )
    return row


def test_first100_candidate_validation_rejects_raw_text_and_gold() -> None:
    bad = _candidate()
    bad["gold_status"] = "gold"
    bad["evidence_text"] = "guidance outlook raw phrase"

    errors = validate_first100_candidate_rows([bad])

    assert any("gold_status" in error for error in errors)
    assert any("raw text field evidence_text" in error for error in errors)


def test_first100_candidate_validation_accepts_metadata_only_pending_row() -> None:
    assert validate_first100_candidate_rows([_candidate()], retrieval_object_ids={"object1"}, evidence_ids={"evidence1"}, chunk_ids={"chunk1"}) == []


def test_first100_candidate_validation_checks_references() -> None:
    errors = validate_first100_candidate_rows([_candidate()], retrieval_object_ids={"other"}, evidence_ids={"other"}, chunk_ids={"other"})

    assert any("retrieval_object_id object1 does not exist" in error for error in errors)
    assert any("evidence_object_id evidence1 does not exist" in error for error in errors)
    assert any("chunk_id chunk1 does not exist" in error for error in errors)
