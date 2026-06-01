from __future__ import annotations

import json
from pathlib import Path

from signal_engine.retrieval.evaluate import load_eval_queries, validate_eval_query_record

REQUIRED_QUERY_FIELDS = {
    "query_id",
    "query_text",
    "query_intent",
    "target_case_id",
    "target_ticker",
    "target_fiscal_period",
    "expected_object_types",
    "expected_signal_types",
    "expected_sections",
    "expected_speaker_roles",
    "expected_evidence_ids",
    "negative_control",
    "abstention_expected",
    "rights_required",
    "notes",
}


def test_hd_eval_queries_include_negative_controls() -> None:
    queries = load_eval_queries(Path("data/retrieval/eval_queries_hd_2025_q4.jsonl"))
    assert len(queries) == 20
    assert all(set(query) == REQUIRED_QUERY_FIELDS for query in queries)
    assert all(not validate_eval_query_record(query) for query in queries)
    assert any(query["abstention_expected"] for query in queries)
    assert any(query["query_intent"] == "trading_request" for query in queries)
    assert any("REVIEW_REQUIRED_HD_2025_Q4_EVIDENCE_ID" in query["expected_evidence_ids"] for query in queries)


def test_first30_template_queries_are_placeholder_bound_and_guardrailed() -> None:
    queries = load_eval_queries(Path("data/retrieval/eval_queries_first30_template.jsonl"))
    assert len(queries) == 50
    assert all(set(query) == REQUIRED_QUERY_FIELDS for query in queries)
    assert all(not validate_eval_query_record(query) for query in queries)
    positives = [query for query in queries if not query["negative_control"]]
    negatives = [query for query in queries if query["negative_control"]]
    assert positives
    assert negatives
    assert all("{reviewed_evidence_id}" in query["expected_evidence_ids"] for query in positives)
    assert all(query["expected_evidence_ids"] == [] for query in negatives)
    assert all(query["abstention_expected"] is True for query in negatives)


def test_query_schema_rejects_unexpected_raw_text_fields() -> None:
    query = json.loads(Path("data/retrieval/eval_queries_hd_2025_q4.jsonl").read_text(encoding="utf-8").splitlines()[0])
    query["raw_text"] = "forbidden"
    errors = validate_eval_query_record(query)
    assert any("raw_text" in error for error in errors)


def test_invalid_query_fixture_rejects_inconsistent_negative_control() -> None:
    query = json.loads(Path("data/retrieval/eval_queries_hd_2025_q4.jsonl").read_text(encoding="utf-8").splitlines()[0])
    query["query_id"] = "invalid_negative_with_expected_id"
    query["negative_control"] = True
    query["abstention_expected"] = True

    errors = validate_eval_query_record(query)

    assert any("negative_control" in error and "expected_evidence_ids" in error for error in errors)


def test_positive_query_fixture_requires_expected_evidence_ids() -> None:
    query = json.loads(Path("data/retrieval/eval_queries_hd_2025_q4.jsonl").read_text(encoding="utf-8").splitlines()[0])
    query["query_id"] = "invalid_positive_without_expected_id"
    query["expected_evidence_ids"] = []

    errors = validate_eval_query_record(query)

    assert any("expected_evidence_ids" in error for error in errors)


def test_query_fixture_rejects_unsafe_claim_wording_for_non_guardrail_rows() -> None:
    query = json.loads(Path("data/retrieval/eval_queries_hd_2025_q4.jsonl").read_text(encoding="utf-8").splitlines()[0])
    query["query_id"] = "invalid_positive_market_claim"
    query["query_text"] = "HD 2025 Q4 buy signal category evidence"

    errors = validate_eval_query_record(query)

    assert any("unsafe market claim" in error for error in errors)


def test_committed_eval_query_jsonl_files_validate_against_v0_contract() -> None:
    for path in sorted(Path("data/retrieval").glob("eval_queries*.jsonl")):
        for row in load_eval_queries(path):
            assert validate_eval_query_record(row) == [], path
