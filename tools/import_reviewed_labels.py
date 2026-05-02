#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from labeling_common import write_csv  # noqa: E402

FIELDS = [
    "candidate_id",
    "case_id",
    "text",
    "weak_label",
    "confidence",
    "noise_flag",
    "review_decision",
    "final_label",
    "reviewer_notes",
]


def import_reviewed_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    imported = []
    for row in rows:
        imported.append({field: str(row.get(field) or "") for field in FIELDS})
    return imported


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import reviewed labels into a normalized reviewed-label CSV.")
    parser.add_argument("--input", default=str(ROOT / "data" / "labeling" / "review_queue.csv"))
    parser.add_argument("--out", default=str(ROOT / "data" / "labeling" / "reviewed_labels.csv"))
    args = parser.parse_args(argv)
    source = Path(args.input)
    if not source.exists():
        raise SystemExit(f"review file not found: {source}")
    rows = import_reviewed_rows(source)
    write_csv(Path(args.out), rows, FIELDS)
    print(f"imported reviewed rows: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
