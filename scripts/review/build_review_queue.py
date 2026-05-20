#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from review.chunking import read_jsonl  # noqa: E402
from review.review_queue import build_review_queue, workload_summary  # noqa: E402


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["rank", "case_id", "chunk_id", "priority_score", "priority_reasons", "suggested_labels", "suggestion_count", "text_preview"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a prioritized review queue from chunk records and weak-label suggestions.")
    parser.add_argument("--records", default=str(ROOT / "data" / "review" / "runtime" / "exports" / "argilla_records.jsonl"))
    parser.add_argument("--suggestions", default=str(ROOT / "data" / "review" / "runtime" / "exports" / "argilla_suggestions.jsonl"))
    parser.add_argument("--out-csv", default=str(ROOT / "data" / "review" / "runtime" / "queue" / "review_queue.csv"))
    parser.add_argument("--summary-out", default=str(ROOT / "data" / "review" / "runtime" / "queue" / "review_queue_summary.json"))
    parser.add_argument("--mode", choices=["top-risk", "random", "stratified"], default="top-risk")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args(argv)
    queue = build_review_queue(read_jsonl(Path(args.records)), read_jsonl(Path(args.suggestions)), mode=args.mode, limit=args.limit)
    _write_csv(Path(args.out_csv), queue)
    Path(args.summary_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.summary_out).write_text(json.dumps(workload_summary(queue), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"queue_rows": len(queue), "output": args.out_csv, "summary": args.summary_out}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
