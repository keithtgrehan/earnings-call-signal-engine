#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.agent1_extraction import deduplicate_candidates


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deduplicate Agent 1 candidate records.")
    parser.add_argument("--in", dest="in_path", default="data/review/staging/agent1_candidates.jsonl")
    parser.add_argument("--out", default="data/review/staging/agent1_candidates_deduped.jsonl")
    parser.add_argument("--report", default="reports/agent1/deduplication_report.csv")
    args = parser.parse_args(argv)
    rows = _load_jsonl(Path(args.in_path))
    deduped = deduplicate_candidates(rows)
    _write_jsonl(Path(args.out), deduped)
    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["input_count", "deduped_count", "duplicates_removed"], lineterminator="\n")
        writer.writeheader()
        writer.writerow({"input_count": len(rows), "deduped_count": len(deduped), "duplicates_removed": len(rows) - len(deduped)})
    print(f"Agent 1 dedupe complete: {len(rows) - len(deduped)} duplicate candidate(s) removed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
