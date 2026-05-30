#!/usr/bin/env python3
"""Evaluate local metadata-only retrieval queries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

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
REPORT_PATH = ROOT / "reports" / "retrieval" / "retrieval_eval_summary.md"


def write_report(summary: dict, out_path: Path = REPORT_PATH) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Retrieval Eval Summary",
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
        f"- Fallback overuse: {summary.get('fallback_overuse', 0.0):.3f}",
        f"- Provenance completeness: {summary.get('provenance_completeness', 1.0):.3f}",
        "- Raw text returned: false",
        f"- smoke_metrics: {str(summary.get('smoke_metrics', True)).lower()}",
        "- evaluated_rag=false",
        "- Evaluation role: evidence-first retrieval gate, not chatbot answer generation",
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate local metadata-only retrieval readiness.")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--objects", type=Path, default=None)
    parser.add_argument("--queries", type=Path, default=DEFAULT_QUERIES)
    parser.add_argument("--out", type=Path, default=REPORT_PATH)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args(argv)
    summary = evaluate_retrieval_objects(args.objects or DEFAULT_OBJECTS, args.queries, limit=args.limit) if args.objects else evaluate_retrieval(args.index, args.queries, limit=args.limit)
    write_report(summary, args.out)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
