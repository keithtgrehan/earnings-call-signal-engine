from __future__ import annotations

from pathlib import Path

from signal_engine.retrieval.evaluate import load_eval_queries


def test_hd_eval_queries_include_negative_controls() -> None:
    queries = load_eval_queries(Path("data/retrieval/eval_queries_hd_2025_q4.jsonl"))
    assert len(queries) >= 5
    assert any(query["expected_abstain"] for query in queries)
    assert any(query.get("unsupported_claim_category") == "trading_advice" for query in queries)
