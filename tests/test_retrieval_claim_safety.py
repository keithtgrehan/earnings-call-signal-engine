from __future__ import annotations

from signal_engine.retrieval.evaluate import evaluate_retrieval_objects


def test_retrieval_eval_does_not_mark_rag_evaluated_without_gates(tmp_path) -> None:
    summary = evaluate_retrieval_objects(tmp_path / "objects.csv", tmp_path / "queries.jsonl")
    assert summary["evaluated_rag"] is False
