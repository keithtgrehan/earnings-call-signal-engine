#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scripts.build_ir_sec_availability_matrix import FIELDNAMES


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate IR/SEC availability matrix output.")
    parser.add_argument("--path", default="reports/agent5/ir_sec_availability_matrix.csv")
    args = parser.parse_args(argv)
    path = ROOT / args.path
    errors: list[str] = []
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except Exception as exc:
        rows = []
        errors.append(str(exc))
    if rows:
        missing = set(FIELDNAMES).difference(rows[0].keys())
        for field in sorted(missing):
            errors.append(f"missing required column {field}")
    for index, row in enumerate(rows, start=1):
        if not row.get("case_id"):
            errors.append(f"row {index}: case_id required")
        if row.get("permitted_ingest_available") not in {"True", "False", True, False}:
            errors.append(f"row {index}: permitted_ingest_available must be boolean-like")
        if row.get("permitted_ingest_available") in {"False", False} and not row.get("blocked_reason_code"):
            errors.append(f"row {index}: unavailable ingest requires blocked_reason_code")
        forbidden = {"raw_text", "raw_body", "transcript_body", "audio_bytes", "video_bytes", "slides_pdf"}.intersection(row)
        for field in sorted(forbidden):
            errors.append(f"row {index}: raw content field {field} is not allowed")
    if errors:
        print(f"IR/SEC availability matrix validation failed: {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"IR/SEC availability matrix validation passed: {len(rows)} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
