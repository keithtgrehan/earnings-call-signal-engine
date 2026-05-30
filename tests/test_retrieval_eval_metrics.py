from __future__ import annotations

import csv
import json
from pathlib import Path

from signal_engine.retrieval.evaluate import evaluate_retrieval_objects
from tools.evaluate_retrieval import _gate_status


def test_retrieval_eval_metrics_from_objects(tmp_path: Path) -> None:
    objects = tmp_path / "objects.csv"
    fields = ["object_id", "object_type", "case_id", "ticker", "company", "fiscal_period", "source_type", "source_ref", "section", "speaker", "topic", "span_start_char", "span_end_char", "source_sha256", "text_sha256", "rights_tier", "retrieval_priority", "commit_allowed", "raw_text_commit_allowed", "raw_text_committed"]
    with objects.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerow({"object_id": "obj1", "object_type": "event_aligned_chunk", "case_id": "hd_2025_q4", "ticker": "HD", "company": "", "fiscal_period": "2025 Q4", "source_type": "chunk", "source_ref": "/desktop/chunk.txt", "section": "prepared_remarks", "speaker": "management", "topic": "guidance", "span_start_char": "0", "span_end_char": "10", "source_sha256": "sha256:" + "a" * 64, "text_sha256": "sha256:" + "b" * 64, "rights_tier": "safe_to_download", "retrieval_priority": "2", "commit_allowed": "false", "raw_text_commit_allowed": "false", "raw_text_committed": "false"})
    queries = tmp_path / "queries.jsonl"
    queries.write_text(json.dumps({"query_id": "q1", "query": "HD guidance management", "case_id": "hd_2025_q4", "ticker": "HD", "fiscal_period": "2025 Q4", "expected_object_ids": ["obj1"], "expected_evidence_ids": [], "expected_abstain": False}) + "\n", encoding="utf-8")
    summary = evaluate_retrieval_objects(objects, queries)
    assert summary["recall_at_1"] == 1.0
    assert summary["raw_text_returned"] is False


def test_evaluated_rag_gate_blocks_fallback_overuse() -> None:
    assert not _gate_status(
        {
            "query_count": 10,
            "recall_at_1": 1.0,
            "citation_validity": 1.0,
            "invalid_citation_rate": 0.0,
            "wrong_case_ticker_period": 0,
            "fallback_overuse": 0.9,
            "raw_text_returned": False,
        }
    )
