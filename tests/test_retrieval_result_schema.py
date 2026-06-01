from __future__ import annotations

import json
from pathlib import Path

from signal_engine.retrieval.evaluate import validate_retrieval_result_record


def test_retrieval_result_schema_requires_no_raw_text() -> None:
    schema = json.loads(Path("schemas/retrieval_result.schema.json").read_text(encoding="utf-8"))
    payload = {
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
        "raw_text_returned": False,
        "citation_valid": True,
        "blocked_reason": None,
        "notes": "metadata-only result",
    }
    assert payload["raw_text_returned"] == schema["properties"]["raw_text_returned"]["const"]
    assert payload["retrieval_method"] in schema["properties"]["retrieval_method"]["enum"]
    assert set(schema["required"]).issubset(payload)
    assert validate_retrieval_result_record(payload) == []


def test_abstention_rows_allow_nullable_object_fields_only_for_abstain_method() -> None:
    row = {
        "query_id": "q1",
        "result_rank": 0,
        "object_id": None,
        "object_type": None,
        "case_id": None,
        "ticker": None,
        "fiscal_period": None,
        "source_hash": None,
        "normalized_transcript_hash": None,
        "provenance_hash": None,
        "section_label": "unknown",
        "speaker_role": "unknown",
        "qa_pair_id": None,
        "retrieval_score": 0.0,
        "retrieval_method": "abstain",
        "citation_valid": True,
        "raw_text_returned": False,
        "blocked_reason": "wrong_ticker",
        "notes": "blocked safely",
    }
    assert validate_retrieval_result_record(row) == []
    row["retrieval_method"] = "bm25"
    assert any("nullable" in error for error in validate_retrieval_result_record(row))


def test_missing_provenance_fails_for_non_abstention_result() -> None:
    row = {
        "query_id": "q1",
        "result_rank": 1,
        "object_id": "obj1",
        "object_type": "evidence_object",
        "case_id": "hd_2025_q4",
        "ticker": "HD",
        "fiscal_period": "2025 Q4",
        "source_hash": "sha256:" + "a" * 64,
        "normalized_transcript_hash": "sha256:" + "b" * 64,
        "provenance_hash": "",
        "section_label": "prepared_remarks",
        "speaker_role": "management",
        "qa_pair_id": "",
        "retrieval_score": 1.0,
        "retrieval_method": "bm25",
        "citation_valid": True,
        "raw_text_returned": False,
        "blocked_reason": None,
        "notes": "metadata-only result",
    }
    assert any("provenance_hash" in error for error in validate_retrieval_result_record(row))


def test_committed_retrieval_eval_results_validate_against_v0_contract() -> None:
    path = Path("data/retrieval/retrieval_eval_results.jsonl")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows
    assert all(validate_retrieval_result_record(row) == [] for row in rows)
