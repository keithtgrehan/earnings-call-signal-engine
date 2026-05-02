#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Import minimally reviewed active-learning labels.")
    parser.add_argument("--input", required=True, help="Reviewed CSV from export_review_batch.py.")
    parser.add_argument("--output", default="data/processed/multimodal_engine/imported_review_labels.jsonl")
    args = parser.parse_args()
    source = Path(args.input)
    if not source.exists():
        raise SystemExit(f"review labels not found: {source}")
    rows = []
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("human_label_signal") or row.get("human_label_emotion"):
                rows.append(row)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + ("\n" if rows else ""),
        encoding="utf-8",
    )
    print(json.dumps({"imported_rows": len(rows), "output": str(target)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
