from __future__ import annotations

import pytest

from signal_engine.retrieval.evaluate import evaluate_retrieval_objects, validate_claim_safety_text


def test_retrieval_eval_does_not_mark_rag_evaluated_without_gates(tmp_path) -> None:
    summary = evaluate_retrieval_objects(tmp_path / "objects.csv", tmp_path / "queries.jsonl")
    assert summary["evaluated_rag"] is False


@pytest.mark.parametrize(
    "claim",
    [
        "buy this stock",
        "sell this stock",
        "short the company",
        "trade on this signal",
        "alpha is proven",
        "causal market reaction is established",
        "statistical significance is proven",
        "live execution should start",
    ],
)
def test_retrieval_claim_safety_rejects_market_claims(claim: str) -> None:
    assert validate_claim_safety_text(claim)
