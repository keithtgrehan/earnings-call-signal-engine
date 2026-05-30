from __future__ import annotations

from signal_engine.retrieval.evaluate import evaluate_retrieval_objects


def test_missing_query_file_is_smoke_not_eval(tmp_path):
    summary = evaluate_retrieval_objects(tmp_path / "missing_objects.csv", tmp_path / "missing_queries.jsonl")
    assert summary["query_count"] == 0
    assert summary["evaluated_rag"] is False
    assert summary["raw_text_returned"] is False
