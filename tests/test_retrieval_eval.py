from __future__ import annotations

import json
from pathlib import Path

from signal_engine.retrieval.evaluate import evaluate_retrieval
from signal_engine.retrieval.index_local import build_local_bm25_index


def test_retrieval_eval_returns_no_raw_text(tmp_path: Path) -> None:
    build_local_bm25_index(
        [
            {
                "object_id": "obj1",
                "ticker": "JPM",
                "section": "prepared_remarks",
                "speaker": "management",
                "topic": "guidance_statement",
                "rights_tier": "safe_to_download",
                "object_type": "event_aligned_chunk",
                "case_id": "case1",
            }
        ],
        out_dir=tmp_path / "index",
    )
    queries = tmp_path / "queries.jsonl"
    queries.write_text(json.dumps({"query_id": "q1", "query": "guidance", "expected_object_ids": ["obj1"]}) + "\n", encoding="utf-8")

    summary = evaluate_retrieval(tmp_path / "index", queries)

    assert summary["hit_count"] == 1
    assert summary["raw_text_returned"] is False
    assert summary["results"][0]["raw_text_returned"] is False
