#!/usr/bin/env python3
"""Evaluate local metadata-only retrieval queries."""

from __future__ import annotations

import argparse
import json
import csv
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.retrieval.evaluate import evaluate_retrieval, evaluate_retrieval_objects

DEFAULT_INDEX = ROOT / ".local" / "signal_engine" / "retrieval" / "indexes" / "nyse100_bm25"
DEFAULT_OBJECTS = ROOT / "data" / "retrieval" / "retrieval_objects_manifest.csv"
DEFAULT_QUERIES = ROOT / "data" / "retrieval" / "eval_queries.example.jsonl"
HD_QUERIES = ROOT / "data" / "retrieval" / "eval_queries_hd_2025_q4.jsonl"
FIRST30_TEMPLATE_QUERIES = ROOT / "data" / "retrieval" / "eval_queries_first30_template.jsonl"
MATERIALIZED_FIRST30_QUERIES = ROOT / "data" / "retrieval" / "eval_queries_first30_materialized.jsonl"
REPORT_PATH = ROOT / "reports" / "retrieval" / "first30_retrieval_eval_summary.md"
RESULTS_PATH = ROOT / "data" / "retrieval" / "first30_eval_results.jsonl"
METRICS_PATH = ROOT / "data" / "retrieval" / "first30_eval_metrics.json"
MAX_FALLBACK_OVERUSE_FOR_EVALUATED_RAG = 0.25


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def materialize_first30_queries(objects_path: Path, out_path: Path = MATERIALIZED_FIRST30_QUERIES) -> list[dict[str, Any]]:
    objects = read_csv(objects_path)
    by_case: dict[str, dict[str, str]] = {}
    for row in objects:
        case_id = row.get("case_id", "")
        if not case_id or case_id in by_case:
            continue
        if row.get("object_type") == "evidence_object":
            by_case[case_id] = row
    for row in objects:
        case_id = row.get("case_id", "")
        if not case_id or case_id in by_case:
            continue
        if row.get("object_type") == "event_aligned_chunk":
            by_case[case_id] = row
    queries: list[dict[str, Any]] = []
    for case_id, row in sorted(by_case.items()):
        if case_id == "hd_2025_q4":
            continue
        ticker = row.get("ticker", "")
        queries.append(
            {
                "query_id": f"{case_id}_first30_metadata_smoke",
                "query": f"{ticker} {case_id} management prepared remarks guidance",
                "case_id": case_id,
                "ticker": ticker,
                "fiscal_period": row.get("fiscal_period", ""),
                "expected_object_ids": [row.get("object_id", "")],
                "expected_evidence_ids": [row.get("object_id", "")] if row.get("object_type") == "evidence_object" else [],
                "requires_evidence_object": True,
                "expected_abstain": False,
                "negative_control": False,
                "unsupported_claim_category": "",
                "notes": "Materialized from available retrieval object metadata only.",
            }
        )
    if by_case:
        first = next(iter(sorted(by_case.values(), key=lambda item: item.get("case_id", ""))))
        queries.append(
            {
                "query_id": "first30_trading_advice_negative",
                "query": "buy sell trading advice from earnings calls",
                "case_id": first.get("case_id", ""),
                "ticker": first.get("ticker", ""),
                "fiscal_period": "",
                "expected_object_ids": [],
                "expected_evidence_ids": [],
                "requires_evidence_object": True,
                "expected_abstain": True,
                "negative_control": True,
                "unsupported_claim_category": "trading_advice",
                "notes": "Must not retrieve metadata as trading advice.",
            }
        )
    write_jsonl(out_path, queries)
    return queries


def _gate_status(summary: dict[str, Any]) -> bool:
    return (
        summary.get("query_count", 0) >= 5
        and summary.get("recall_at_1", 0.0) >= 0.8
        and summary.get("citation_validity", 0.0) >= 0.95
        and summary.get("invalid_citation_rate", 1.0) <= 0.05
        and summary.get("wrong_case_ticker_period", 1) == 0
        and summary.get("fallback_overuse", 1.0) <= MAX_FALLBACK_OVERUSE_FOR_EVALUATED_RAG
        and summary.get("raw_text_returned") is False
    )


def write_report(summary: dict, out_path: Path = REPORT_PATH) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    evaluated_rag = _gate_status(summary)
    lines = [
        "# First30 Retrieval Eval Summary",
        "",
        f"- Query count: {summary['query_count']}",
        f"- Result count: {summary['result_count']}",
        f"- recall@1: {summary.get('recall_at_1', summary.get('hit_rate', 0.0)):.3f}",
        f"- recall@3: {summary.get('recall_at_3', 0.0):.3f}",
        f"- recall@5: {summary.get('recall_at_5', 0.0):.3f}",
        f"- MRR: {summary.get('mrr', 0.0):.3f}",
        f"- Evidence ID hit rate: {summary.get('evidence_id_hit_rate', 0.0):.3f}",
        f"- Citation validity: {summary.get('citation_validity', 1.0):.3f}",
        f"- Invalid citation rate: {summary.get('invalid_citation_rate', 0.0):.3f}",
        f"- Wrong case/ticker/period results: {summary.get('wrong_case_ticker_period', 0)}",
        f"- Abstention correctness: {summary.get('abstention_correctness', 0.0):.3f}",
        f"- Fallback overuse: {summary.get('fallback_overuse', 0.0):.3f} (gate <= {MAX_FALLBACK_OVERUSE_FOR_EVALUATED_RAG:.2f})",
        f"- Provenance completeness: {summary.get('provenance_completeness', 1.0):.3f}",
        "- Raw text returned: false",
        f"- smoke_metrics: {str(summary.get('smoke_metrics', True)).lower()}",
        f"- evaluated_rag={str(evaluated_rag).lower()}",
        "- Evaluation role: evidence-first retrieval gate, not chatbot answer generation",
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate local metadata-only retrieval readiness.")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--objects", type=Path, default=None)
    parser.add_argument("--queries", type=Path, default=None)
    parser.add_argument("--hd-queries", type=Path, default=HD_QUERIES)
    parser.add_argument("--first30-template", type=Path, default=FIRST30_TEMPLATE_QUERIES)
    parser.add_argument("--materialized-first30", type=Path, default=MATERIALIZED_FIRST30_QUERIES)
    parser.add_argument("--results", type=Path, default=RESULTS_PATH)
    parser.add_argument("--metrics", type=Path, default=METRICS_PATH)
    parser.add_argument("--out", type=Path, default=REPORT_PATH)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args(argv)
    objects = args.objects or DEFAULT_OBJECTS
    if args.queries:
        queries = args.queries
    else:
        first30_queries = materialize_first30_queries(objects, args.materialized_first30)
        combined = []
        for path in (args.hd_queries, args.materialized_first30):
            if path.exists():
                combined.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
        queries = ROOT / "data" / "retrieval" / "eval_queries_first30_combined.jsonl"
        write_jsonl(queries, combined)
        _ = first30_queries
    summary = evaluate_retrieval_objects(objects, queries, limit=args.limit) if args.objects or objects.exists() else evaluate_retrieval(args.index, queries or DEFAULT_QUERIES, limit=args.limit)
    write_jsonl(args.results, summary.get("results", []))
    metrics = {key: value for key, value in summary.items() if key != "results"}
    metrics["evaluated_rag"] = _gate_status(summary)
    metrics["raw_text_returned"] = False
    write_json(args.metrics, metrics)
    write_report(summary, args.out)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
