#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def validate_segments(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"rows": 0, "errors": [{"row": 0, "error": "segments file missing"}]}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    errors: list[dict[str, object]] = []
    for index, row in enumerate(rows, start=2):
        try:
            if float(row.get("end_time_sec", "0")) < float(row.get("start_time_sec", "0")):
                errors.append({"row": index, "error": "end_time_sec before start_time_sec"})
        except ValueError:
            errors.append({"row": index, "error": "segment timestamps must be numeric"})
        if row.get("raw_text_committed") != "false":
            errors.append({"row": index, "error": "raw_text_committed must be false"})
    return {"rows": len(rows), "errors": errors}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate repo-safe ASR segment metadata.")
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    summary = validate_segments(args.path)
    print(f"asr_segments rows={summary['rows']} errors={len(summary['errors'])}")
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
