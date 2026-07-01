#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate_rows(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    if len(rows) < 100:
        errors.append("call target matrix must contain at least 100 rows")
    for index, row in enumerate(rows, start=1):
        case_id = row.get("case_id", "")
        if case_id in seen:
            errors.append(f"row {index}: duplicate case_id {case_id}")
        seen.add(case_id)
        if row.get("exchange") != "NYSE":
            errors.append(f"row {index}: exchange must be NYSE")
        if row.get("target_year") not in {"2025", "2024", "2023", "2022", "2021"}:
            errors.append(f"row {index}: target_year outside 2025-backward five-year window")
        if row.get("event_identity_status") == "target_placeholder_period_end_date":
            if "not a discovered earnings-call date" not in row.get("notes", ""):
                errors.append(f"row {index}: placeholder event dates must be clearly marked")
        elif not row.get("event_date"):
            errors.append(f"row {index}: discovered events require event_date")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=ROOT / "data/acquisition/nyse_100_5y_call_targets.csv")
    args = parser.parse_args()
    with args.path.open(newline="", encoding="utf-8") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    errors = validate_rows(rows)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"NYSE 100 call target validation passed: {args.path}")


if __name__ == "__main__":
    main()
