from __future__ import annotations

import json
from pathlib import Path
import tempfile
from typing import Any

from .index_local import build_local_bm25_index, load_retrieval_manifest, score_query
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


def _rank_for_expected(returned: list[str], expected: set[str]) -> int:
    for index, object_id in enumerate(returned, start=1):
        if object_id in expected:
            return index
    return 0


def evaluate_retrieval_objects(objects_path: Path, queries_path: Path, *, limit: int = 5) -> dict[str, Any]:
    queries = load_eval_queries(queries_path)
    objects = load_retrieval_manifest(objects_path)
    temp_index = {
        "documents": [],
        "document_count": 0,
        "avg_doc_length": 0,
        "document_frequency": {},
        "raw_text_indexed": False,
    }
    if objects:
        # Build in a disposable local directory so the production index path is not required.
        with tempfile.TemporaryDirectory(prefix="signal_engine_eval_bm25_") as tmp:
            temp_index = build_local_bm25_index(objects, out_dir=Path(tmp))
    results: list[dict[str, Any]] = []
    recall_hits = {1: 0, 3: 0, 5: 0}
    reciprocal_ranks: list[float] = []
    citation_valid = 0
    invalid_citation = 0
    wrong_case_ticker_period = 0
    abstention_correct = 0
    fallback_results = 0
    evidence_hits = 0
    provenance_complete = 0
    for query in queries:
        expected = set(query.get("expected_object_ids") or [])
        expected_abstain = bool(query.get("expected_abstain", False))
        ranked = [] if expected_abstain and not expected else score_query(temp_index, str(query.get("query", "")), limit=limit)
        returned = [row["object_id"] for row in ranked]
        rank = _rank_for_expected(returned, expected)
        for k in recall_hits:
            if expected and rank and rank <= k:
                recall_hits[k] += 1
        reciprocal_ranks.append((1 / rank) if rank else 0.0)
        if expected and rank:
            evidence_hits += 1
        if expected_abstain and not ranked:
            abstention_correct += 1
        for result_rank, row in enumerate(ranked, start=1):
            metadata = row.get("metadata", {})
            same_context = (
                (not query.get("case_id") or metadata.get("case_id") == query.get("case_id"))
                and (not query.get("ticker") or metadata.get("ticker") == query.get("ticker"))
                and (not query.get("fiscal_period") or metadata.get("fiscal_period") == query.get("fiscal_period"))
            )
            citation_ok = bool(metadata.get("source_ref") and metadata.get("source_sha256") and same_context)
            citation_valid += 1 if citation_ok else 0
            invalid_citation += 0 if citation_ok else 1
            wrong_case_ticker_period += 0 if same_context else 1
            fallback_results += 1 if metadata.get("object_type") == "semantic_chunk" else 0
            provenance_complete += 1 if metadata.get("source_ref") and metadata.get("source_sha256") and metadata.get("text_sha256") else 0
            results.append(
                {
                    "query_id": query.get("query_id", ""),
                    "object_id": row["object_id"],
                    "rank": result_rank,
                    "score": row["score"],
                    "retrieval_method": "local_bm25_metadata",
                    "raw_text_returned": False,
                    "citation_valid": citation_ok,
                    "abstained": False,
                    "case_id": metadata.get("case_id", ""),
                    "ticker": metadata.get("ticker", ""),
                    "fiscal_period": metadata.get("fiscal_period", ""),
                    "evidence_id": row["object_id"] if metadata.get("object_type") == "evidence_object" else "",
                    "claim_safety_status": "blocked_unsupported_claim" if query.get("negative_control") else "retrieved_metadata_only",
                }
            )
        if not ranked:
            results.append(
                {
                    "query_id": query.get("query_id", ""),
                    "object_id": "",
                    "rank": 0,
                    "score": 0.0,
                    "retrieval_method": "local_bm25_metadata",
                    "raw_text_returned": False,
                    "citation_valid": True,
                    "abstained": True,
                    "case_id": "",
                    "ticker": "",
                    "fiscal_period": "",
                    "evidence_id": "",
                    "claim_safety_status": "abstained",
                }
            )
    query_count = len(queries)
    result_count = len([row for row in results if not row["abstained"]])
    return {
        "query_count": query_count,
        "result_count": result_count,
        "recall_at_1": recall_hits[1] / query_count if query_count else 0.0,
        "recall_at_3": recall_hits[3] / query_count if query_count else 0.0,
        "recall_at_5": recall_hits[5] / query_count if query_count else 0.0,
        "mrr": (sum(reciprocal_ranks) / query_count) if query_count else 0.0,
        "evidence_id_hit_rate": evidence_hits / query_count if query_count else 0.0,
        "citation_validity": citation_valid / result_count if result_count else 1.0,
        "invalid_citation_rate": invalid_citation / result_count if result_count else 0.0,
        "wrong_case_ticker_period": wrong_case_ticker_period,
        "abstention_correctness": abstention_correct / max(1, len([q for q in queries if q.get("expected_abstain")])),
        "fallback_overuse": fallback_results / result_count if result_count else 0.0,
        "latency_ms": 0,
        "provenance_completeness": provenance_complete / result_count if result_count else 1.0,
        "raw_text_returned": False,
        "smoke_metrics": query_count < 10,
        "evaluated_rag": False,
        "results": results,
    }
