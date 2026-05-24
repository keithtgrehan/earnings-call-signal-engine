#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.acquisition.nyse100 import CHUNK_FIELDS

def validate_rows(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        if list(row.keys()) != CHUNK_FIELDS:
            errors.append(f"row {index}: invalid chunk manifest fields")
        if row.get("chunk_id") in seen:
            errors.append(f"row {index}: duplicate chunk_id")
        seen.add(row.get("chunk_id", ""))
        if row.get("raw_text_committed") != "false":
            errors.append(f"row {index}: raw_text_committed must be false")
        if row.get("rights_status") not in {"safe_to_download", "manual_local_review_only"}:
            errors.append(f"row {index}: invalid chunk rights_status")
        if not row.get("text_sha256", "").startswith("sha256:"):
            errors.append(f"row {index}: text_sha256 required")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=ROOT / "data/acquisition/nyse_100_chunk_manifest.csv")
    args = parser.parse_args()
    if not args.path.exists():
        raise SystemExit(f"chunk manifest missing: {args.path}")
    with args.path.open(newline="", encoding="utf-8") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    errors = validate_rows(rows)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"NYSE 100 chunk manifest validation passed: {args.path} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
