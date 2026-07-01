from __future__ import annotations

from pathlib import Path

import pytest

from signal_engine.retrieval.evaluate import (
    validate_eval_query_record,
    validate_no_forbidden_payload_keys,
    validate_retrieval_result_record,
)


def test_retrieval_manifests_do_not_expose_raw_text_column() -> None:
    header = Path("data/retrieval/retrieval_objects_manifest.csv").read_text(encoding="utf-8").splitlines()[0]
    assert "evidence_text" not in header
    assert "raw_text_committed" in header


@pytest.mark.parametrize(
    "forbidden_key",
    ["raw_text", "transcript_text", "asr_text", "audio_text", "chunk_text", "embedding", "embeddings", "vector", "vectors", "vector_db", "payload_text"],
)
def test_forbidden_raw_payload_keys_fail(forbidden_key: str) -> None:
    errors = validate_no_forbidden_payload_keys({forbidden_key: "blocked"}, context="result")
    assert errors
    assert forbidden_key in errors[0]


def test_forbidden_raw_payload_keys_fail_when_camel_cased() -> None:
    errors = validate_no_forbidden_payload_keys({"payloadText": "blocked"}, context="result")
    assert errors
    assert "payloadText" in errors[0]


def test_eval_query_rejects_transcript_like_text_values() -> None:
    query = {
        "query_id": "q1",
        "query_text": "HD 2025 Q4 prepared remarks guidance category evidence",
        "query_intent": "prepared_guidance",
        "target_case_id": "hd_2025_q4",
        "target_ticker": "HD",
        "target_fiscal_period": "2025 Q4",
        "expected_object_types": ["evidence_object"],
        "expected_signal_types": ["guidance"],
        "expected_sections": ["prepared_remarks"],
        "expected_speaker_roles": ["management"],
        "expected_evidence_ids": ["evidence_1"],
        "negative_control": False,
        "abstention_expected": False,
        "rights_required": ["retrieval_object_manifest"],
        "notes": "Speaker: [redacted transcript-like payload]",
    }

    errors = validate_eval_query_record(query)

    assert any("transcript-like text" in error for error in errors)


def test_retrieval_result_rejects_chunk_like_text_values() -> None:
    result = {
        "query_id": "q1",
        "result_rank": 1,
        "object_id": "obj1",
        "object_type": "evidence_object",
        "case_id": "hd_2025_q4",
        "ticker": "HD",
        "fiscal_period": "2025 Q4",
        "source_hash": "sha256:" + "a" * 64,
        "normalized_transcript_hash": "sha256:" + "b" * 64,
        "provenance_hash": "sha256:" + "c" * 64,
        "section_label": "prepared_remarks",
        "speaker_role": "management",
        "qa_pair_id": "",
        "retrieval_score": 1.0,
        "retrieval_method": "bm25",
        "citation_valid": True,
        "raw_text_returned": False,
        "blocked_reason": None,
        "notes": "chunk text excerpt: [redacted retrieval payload]",
    }

    errors = validate_retrieval_result_record(result)

    assert any("raw/chunk text" in error for error in errors)
