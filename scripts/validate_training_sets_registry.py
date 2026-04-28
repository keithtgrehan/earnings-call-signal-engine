#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = (
    "dataset_id",
    "dataset_name",
    "dataset_type",
    "source_category",
    "intended_use",
    "status",
    "license_check_required",
    "contains_real_company_data",
    "contains_pii_risk",
    "local_path",
    "external_reference",
    "notes",
)

VALID_STATUSES = {"planned", "candidate", "example", "blocked", "promoted"}
VALID_SOURCE_CATEGORIES = {
    "manual_review",
    "handcrafted_example",
    "public_research",
    "sec_edgar",
    "kaggle",
    "transcript_vendor",
}
BOOLEAN_FIELDS = {"license_check_required", "contains_real_company_data", "contains_pii_risk"}


def detect_format(path: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    if path.suffix.lower() == ".csv":
        return "csv"
    if path.suffix.lower() == ".json":
        return "json"
    raise ValueError("Could not infer format from extension; pass --format csv or --format json.")


def load_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict) and isinstance(payload.get("datasets"), list):
        rows = payload["datasets"]
    else:
        raise ValueError("Training-set registry must be a list or an object with a datasets list.")
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError("Every training-set registry row must be an object.")
    return rows


def valid_bool(value: Any, *, registry_format: str) -> bool:
    if registry_format == "json":
        return isinstance(value, bool)
    return value in {"true", "false"}


def validate_rows(rows: list[dict[str, Any]], *, registry_format: str) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        for field in REQUIRED_FIELDS:
            if field not in row:
                errors.append(f"row {index}: missing required field {field}")
        dataset_id = str(row.get("dataset_id", "")).strip()
        if not dataset_id:
            errors.append(f"row {index}: dataset_id is required")
        elif dataset_id in seen:
            errors.append(f"row {index}: duplicate dataset_id {dataset_id!r}")
        seen.add(dataset_id)
        if "status" in row and row["status"] not in VALID_STATUSES:
            errors.append(f"row {index}: invalid status {row['status']!r}")
        if "source_category" in row and row["source_category"] not in VALID_SOURCE_CATEGORIES:
            errors.append(f"row {index}: invalid source_category {row['source_category']!r}")
        for field in BOOLEAN_FIELDS:
            if field in row and not valid_bool(row[field], registry_format=registry_format):
                errors.append(f"row {index}: invalid boolean {field} {row[field]!r}; expected true/false")
    return errors


def build_summary(path: Path, *, requested_format: str) -> dict[str, Any]:
    registry_format = detect_format(path, requested_format)
    rows = load_csv(path) if registry_format == "csv" else load_json(path)
    errors = validate_rows(rows, registry_format=registry_format)
    return {
        "status": "valid" if not errors else "invalid",
        "path": str(path),
        "format": registry_format,
        "row_count": len(rows),
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Signal Engine training/evaluation set registry.")
    parser.add_argument("--path", required=True, help="Registry CSV or JSON path.")
    parser.add_argument("--format", choices=("csv", "json", "auto"), default="auto")
    parser.add_argument("--json-out", help="Optional JSON summary output path.")
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
        print(
            f"Training-set registry validation failed: "
            f"{summary['row_count']} row(s), {len(summary['errors'])} error(s)."
        )
        for error in summary["errors"]:
            print(f"- {error}")
        return 1

    print(f"Training-set registry validation passed: {summary['row_count']} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
