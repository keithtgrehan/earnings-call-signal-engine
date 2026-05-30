from __future__ import annotations

from signal_engine.first30_extraction import CANDIDATE_FIELDS, validate_candidate_rows


def _candidate() -> dict[str, str]:
    return {
        field: ""
        for field in CANDIDATE_FIELDS
    } | {
        "candidate_id": "cand1",
        "case_id": "hd_2025_q4",
        "ticker": "HD",
        "fiscal_period": "2025 Q4",
        "label": "uncertainty",
        "rule_id": "uncertainty_terms",
        "confidence": "0.64",
        "review_status": "pending_human_review",
        "gold_status": "not_gold",
        "source_ref": "/desktop/chunk.txt",
        "source_sha256": "sha256:" + "a" * 64,
        "normalized_transcript_sha256": "sha256:" + "b" * 64,
        "retrieval_object_id": "obj1",
        "text_hash": "sha256:" + "c" * 64,
        "provenance_hash": "sha256:" + "d" * 64,
        "raw_text_committed": "false",
        "commit_allowed": "false",
        "training_allowed": "false",
    }


def test_candidate_validation_rejects_gold_or_raw_text() -> None:
    bad = _candidate()
    bad["gold_status"] = "gold"
    bad["snippet"] = "guidance outlook raw phrase"

    errors = validate_candidate_rows([bad])

    assert any("gold_status" in error for error in errors)
    assert any("raw evidence-like text" in error for error in errors)


def test_candidate_validation_accepts_metadata_only_pending_candidate() -> None:
    assert validate_candidate_rows([_candidate()]) == []
