from __future__ import annotations

from pathlib import Path

from signal_engine.retrieval.evaluate import evaluate_retrieval_objects, write_jsonl


def test_missing_query_file_is_smoke_not_eval(tmp_path):
    summary = evaluate_retrieval_objects(tmp_path / "missing_objects.csv", tmp_path / "missing_queries.jsonl")
    assert summary["query_count"] == 0
    assert summary["evaluated_rag"] is False
    assert summary["raw_text_returned"] is False


def _guardrail_query(query_id: str, intent: str) -> dict[str, object]:
    return {
        "query_id": query_id,
        "query_text": f"HD {intent} metadata category request",
        "query_intent": intent,
        "target_case_id": "hd_2025_q4",
        "target_ticker": "HD",
        "target_fiscal_period": "2025 Q4",
        "expected_object_types": [],
        "expected_signal_types": [],
        "expected_sections": [],
        "expected_speaker_roles": [],
        "expected_evidence_ids": [],
        "negative_control": True,
        "abstention_expected": True,
        "rights_required": ["retrieval_object_manifest"],
        "notes": "guardrail abstention expected",
    }


def test_suppression_guardrails_abstain_with_blocked_reasons(tmp_path: Path) -> None:
    queries = tmp_path / "queries.jsonl"
    write_jsonl(
        queries,
        [
            _guardrail_query("wrong_ticker", "wrong_ticker"),
            _guardrail_query("wrong_period", "wrong_period"),
            _guardrail_query("safe_harbor", "safe_harbor_suppressed"),
            _guardrail_query("non_gaap", "non_gaap_suppressed"),
            _guardrail_query("operator_only", "operator_only_suppressed"),
            _guardrail_query("vendor_disclaimer", "vendor_disclaimer_suppressed"),
            _guardrail_query("audio_unmatched", "audio_unmatched"),
            _guardrail_query("trading", "trading_request"),
        ],
    )
    summary = evaluate_retrieval_objects(tmp_path / "objects.csv", queries)
    reasons = {row["blocked_reason"] for row in summary["results"]}
    assert reasons == {
        "wrong_ticker",
        "wrong_period",
        "safe_harbor_suppressed",
        "non_gaap_suppressed",
        "operator_only_suppressed",
        "vendor_disclaimer_suppressed",
        "audio_unmatched",
        "trading_request",
    }
    assert summary["rates"]["abstention_correctness"] == {"numerator": 8, "denominator": 8, "percentage": 100.0}
