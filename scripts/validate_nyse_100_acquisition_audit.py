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

from signal_engine.acquisition.nyse100 import AUDIT_FIELDS
from signal_engine.acquisition.rights import RIGHTS_STATUSES


def validate_audit_rows(rows: list[dict[str, str]], *, audit_path: Path) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    if not rows:
        errors.append("audit CSV must contain at least one row")
    for index, row in enumerate(rows, start=1):
        if list(row.keys()) != AUDIT_FIELDS:
            errors.append(f"row {index}: audit fields do not match required schema")
        case_id = row.get("case_id", "")
        if case_id in seen:
            errors.append(f"row {index}: duplicate case_id {case_id}")
        seen.add(case_id)
        if row.get("exchange") != "NYSE":
            errors.append(f"row {index}: exchange must be NYSE")
        if row.get("rights_status") not in RIGHTS_STATUSES:
            errors.append(f"row {index}: invalid rights_status {row.get('rights_status')!r}")
        if row.get("priority_tier") not in {"1", "2", "3", "4"}:
            errors.append(f"row {index}: invalid priority_tier")
        if row.get("rights_status") in {"blocked", "unknown_fail_closed", "license_required"} and not row.get("blocked_reason"):
            errors.append(f"row {index}: blocked rows require blocked_reason")
        if row.get("local_paths_created") == "true":
            for field in ("transcript_local_path", "audio_local_path", "video_local_path"):
                if not Path(row.get(field, "")).exists():
                    errors.append(f"row {index}: local path missing for {field}")
        if "youtube.com" in row.get("audio_local_path", "").lower() or "youtube.com" in row.get("video_local_path", "").lower():
            errors.append(f"row {index}: YouTube media path must not be local downloaded media")
    if audit_path.exists() and audit_path.name != "nyse_earnings_call_audit.csv":
        errors.append("audit file should be named nyse_earnings_call_audit.csv")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", type=Path, required=True)
    args = parser.parse_args()
    with args.audit.open(newline="", encoding="utf-8") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    errors = validate_audit_rows(rows, audit_path=args.audit)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"NYSE 100 acquisition audit validation passed: {args.audit}")


if __name__ == "__main__":
    main()
