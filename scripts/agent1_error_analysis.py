#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import argparse
import csv
import json
from pathlib import Path


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_counts(path: Path, header: str, counts: Counter[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[header, "count"], lineterminator="\n")
        writer.writeheader()
        for key, count in sorted(counts.items()):
            writer.writerow({header: key, "count": count})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write Agent 1 candidate completeness and false-positive bucket reports.")
    parser.add_argument("--in", dest="in_path", default="data/review/staging/agent1_review_queue.jsonl")
    args = parser.parse_args(argv)
    rows = _load_jsonl(Path(args.in_path))
    _write_counts(Path("reports/agent1/false_positive_buckets.csv"), "false_positive_bucket", Counter(str(row.get("false_positive_bucket", "")) or "none" for row in rows))
    completeness = Counter("complete" if row.get("provenance_hash") and row.get("evidence_span_ref") else "missing" for row in rows)
    _write_counts(Path("reports/agent1/evidence_completeness.csv"), "evidence_status", completeness)
    print(f"Agent 1 error analysis complete: {len(rows)} candidate row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
