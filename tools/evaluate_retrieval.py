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

from signal_engine.retrieval.evaluate import evaluate_retrieval

DEFAULT_INDEX = ROOT / ".local" / "signal_engine" / "retrieval" / "indexes" / "nyse100_bm25"
DEFAULT_QUERIES = ROOT / "data" / "retrieval" / "eval_queries.example.jsonl"
REPORT_PATH = ROOT / "reports" / "retrieval" / "retrieval_eval_summary.md"


def write_report(summary: dict) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Retrieval Eval Summary",
        "",
        f"- Query count: {summary['query_count']}",
        f"- Result count: {summary['result_count']}",
        f"- Hit count: {summary['hit_count']}",
        f"- Hit rate: {summary['hit_rate']:.3f}",
        "- Raw text returned: false",
        "- Evaluation role: readiness smoke check only",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate local metadata-only retrieval readiness.")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--queries", type=Path, default=DEFAULT_QUERIES)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args(argv)
    summary = evaluate_retrieval(args.index, args.queries, limit=args.limit)
    write_report(summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
