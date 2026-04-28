#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = (
    "case_id",
    "ticker",
    "company_name",
    "fiscal_period",
    "call_date",
    "source_category",
    "source_url",
    "transcript_path",
    "audio_available",
    "video_available",
    "transcript_status",
    "label_status",
    "review_status",
    "case_type",
    "notes",
)

ENUMS = {
    "source_category": {"investor_relations", "sec_edgar", "exchange_site", "transcript_vendor", "manual_placeholder"},
    "transcript_status": {"missing", "placeholder", "downloaded", "parsed", "validated", "blocked"},
    "label_status": {"unlabeled", "weak_labeled", "manually_labeled", "reviewed"},
    "review_status": {"not_started", "in_progress", "reviewed", "rejected"},
    "case_type": {"guidance_change", "stable_control", "messy_ambiguous"},
}

BOOLEAN_FIELDS = {"audio_available", "video_available"}


def _detect_format(path: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    if path.suffix.lower() == ".csv":
        return "csv"
    if path.suffix.lower() == ".json":
        return "json"
    raise ValueError("Could not infer format from extension; pass --format csv or --format json.")


def _load_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_json(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict) and isinstance(payload.get("cases"), list):
        rows = payload["cases"]
    else:
        raise ValueError("JSON manifest must be a list or an object with a cases list.")
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError("Every JSON manifest row must be an object.")
    return rows


def _valid_bool(value: Any, *, manifest_format: str) -> bool:
    if manifest_format == "json":
        return isinstance(value, bool)
    return value in {"true", "false"}


def validate_rows(rows: list[dict[str, Any]], *, manifest_format: str) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        for field in REQUIRED_FIELDS:
            if field not in row:
                errors.append(f"row {index}: missing required field {field}")
        case_id = str(row.get("case_id", "")).strip()
        if not case_id:
            errors.append(f"row {index}: case_id is required")
        for field, valid_values in ENUMS.items():
            if field in row and row[field] not in valid_values:
                errors.append(f"row {index}: invalid {field} {row[field]!r}")
        for field in BOOLEAN_FIELDS:
            if field in row and not _valid_bool(row[field], manifest_format=manifest_format):
                errors.append(f"row {index}: invalid boolean {field} {row[field]!r}; expected true/false")
    return errors


def build_summary(path: Path, *, requested_format: str) -> dict[str, Any]:
    manifest_format = _detect_format(path, requested_format)
    rows = _load_csv(path) if manifest_format == "csv" else _load_json(path)
    errors = validate_rows(rows, manifest_format=manifest_format)
    return {
        "status": "valid" if not errors else "invalid",
        "path": str(path),
        "format": manifest_format,
        "row_count": len(rows),
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Signal Engine corpus manifest CSV or JSON file.")
    parser.add_argument("--path", required=True, help="Manifest path to validate.")
    parser.add_argument("--format", choices=("csv", "json", "auto"), default="auto")
    parser.add_argument("--json-out", help="Optional path for machine-readable validation summary.")
    args = parser.parse_args(argv)

    try:
        summary = build_summary(Path(args.path), requested_format=args.format)
    except Exception as exc:
        summary = {
            "status": "invalid",
            "path": args.path,
            "format": args.format,
            "row_count": 0,
            "errors": [str(exc)],
        }

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    if summary["errors"]:
        print(f"Corpus manifest validation failed: {summary['row_count']} row(s), {len(summary['errors'])} error(s).")
        for error in summary["errors"]:
            print(f"- {error}")
        return 1
    print(f"Corpus manifest validation passed: {summary['row_count']} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
