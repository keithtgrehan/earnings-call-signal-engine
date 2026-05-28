from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .query import query_local_index


def load_eval_queries(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def evaluate_retrieval(index_path: Path, queries_path: Path, *, limit: int = 10) -> dict[str, Any]:
    queries = load_eval_queries(queries_path)
    results: list[dict[str, Any]] = []
    hits = 0
    for query in queries:
        ranked = query_local_index(index_path, str(query.get("query", "")), limit=limit)
        expected = set(query.get("expected_object_ids") or [])
        returned = [row["object_id"] for row in ranked]
        if expected and expected.intersection(returned):
            hits += 1
        for rank, row in enumerate(ranked, start=1):
            results.append(
                {
                    "query_id": query.get("query_id", ""),
                    "object_id": row["object_id"],
                    "rank": rank,
                    "score": row["score"],
                    "retrieval_method": "local_bm25_metadata",
                    "raw_text_returned": False,
                }
            )
    return {
        "query_count": len(queries),
        "result_count": len(results),
        "hit_count": hits,
        "hit_rate": (hits / len(queries)) if queries else 0.0,
        "results": results,
        "raw_text_returned": False,
    }
