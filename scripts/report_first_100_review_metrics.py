#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.gold_review import summarize_review_metrics


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report first-100 review metrics without writing canonical gold labels.")
    parser.add_argument("--queue", default="data/review/staging/first_100_review_queue.jsonl")
    parser.add_argument("--promotion-manifest", default="data/review/staging/promotion_manifest.jsonl")
    parser.add_argument("--out-json", default="reports/review/first_100_review_metrics.json")
    parser.add_argument("--out-md", default="reports/review/first_100_review_metrics.md")
    args = parser.parse_args(argv)
    queue_rows = _load_jsonl(Path(args.queue))
    promotion_rows = _load_jsonl(Path(args.promotion_manifest))
    summary = summarize_review_metrics(queue_rows, promotion_rows)
    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# First-100 Review Metrics",
        "",
        "Metrics are review workflow status only. They do not mutate canonical gold labels.",
        "",
        f"- Queue size: `{summary['queue_size']}`",
        f"- Promotion candidates: `{summary['promotion_candidate_count']}`",
        "",
        "## Review Status Counts",
    ]
    for status, count in summary["review_status_counts"].items():
        lines.append(f"- `{status}`: `{count}`")
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"First-100 review metrics written: {summary['queue_size']} queue row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
