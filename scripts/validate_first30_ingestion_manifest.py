#!/usr/bin/env python3
"""Validate the first30 transcript ingestion manifest guardrails."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "data" / "acquisition" / "first30_transcript_ingestion_manifest.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def validate_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    rows = read_csv(path)
    errors: list[str] = []
    if not rows:
        errors.append("manifest has no rows")
    seen: set[str] = set()
    for index, row in enumerate(rows, start=2):
        case_id = row.get("case_id", "")
        if not case_id:
            errors.append(f"row {index}: case_id required")
        if case_id in seen:
            errors.append(f"row {index}: duplicate case_id {case_id}")
        seen.add(case_id)
        if row.get("exchange") != "NYSE":
            errors.append(f"row {index}: exchange must be NYSE")
        if row.get("commit_allowed") != "false":
            errors.append(f"row {index}: commit_allowed must be false")
        if row.get("training_allowed") != "false":
            errors.append(f"row {index}: training_allowed must be false")
        if row.get("raw_text_committed") != "false":
            errors.append(f"row {index}: raw_text_committed must be false")
        if row.get("download_allowed") == "true" and row.get("blocked_reason"):
            errors.append(f"row {index}: download_allowed row has blocked_reason")
        if row.get("download_allowed") == "true" and not row.get("approval_ref"):
            errors.append(f"row {index}: download_allowed row requires approval_ref")
        if row.get("source_url_kind") == "official_ir_cdn_direct" and row.get("rights_review_required") != "true":
            errors.append(f"row {index}: official IR CDN rows require rights_review_required=true")
    return {
        "path": str(path),
        "rows": len(rows),
        "download_allowed": sum(1 for row in rows if row.get("download_allowed") == "true"),
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate first30 transcript ingestion manifest.")
    parser.add_argument("--path", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args(argv)
    summary = validate_manifest(args.path)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
