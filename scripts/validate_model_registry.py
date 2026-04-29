#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = (
    "model_id",
    "model_name",
    "model_type",
    "status",
    "intended_use",
    "requires_external_api",
    "requires_local_download",
    "model_weights_committed",
    "validated",
    "notes",
)

VALID_STATUSES = {"implemented", "candidate", "planned", "blocked"}
BOOLEAN_FIELDS = {
    "requires_external_api",
    "requires_local_download",
    "model_weights_committed",
    "validated",
}


def load_registry(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict) and isinstance(payload.get("models"), list):
        rows = payload["models"]
    else:
        raise ValueError("Model registry must be a list or an object with a models list.")
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError("Every model registry row must be an object.")
    return rows


def validate_rows(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        for field in REQUIRED_FIELDS:
            if field not in row:
                errors.append(f"row {index}: missing required field {field}")
        model_id = str(row.get("model_id", "")).strip()
        if not model_id:
            errors.append(f"row {index}: model_id is required")
        elif model_id in seen:
            errors.append(f"row {index}: duplicate model_id {model_id!r}")
        seen.add(model_id)
        if "status" in row and row["status"] not in VALID_STATUSES:
            errors.append(f"row {index}: invalid status {row['status']!r}")
        for field in BOOLEAN_FIELDS:
            if field in row and not isinstance(row[field], bool):
                errors.append(f"row {index}: {field} must be a JSON boolean")
        if row.get("model_weights_committed") is True:
            errors.append(f"row {index}: model_weights_committed must be false")
        if row.get("validated") is True and row.get("status") != "implemented":
            errors.append(f"row {index}: non-implemented models cannot be marked validated")
    return errors


def build_summary(path: Path) -> dict[str, Any]:
    rows = load_registry(path)
    errors = validate_rows(rows)
    return {
        "status": "valid" if not errors else "invalid",
        "path": str(path),
        "row_count": len(rows),
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Signal Engine model registry JSON file.")
    parser.add_argument("--path", required=True, help="Model registry JSON path.")
    parser.add_argument("--json-out", help="Optional JSON summary output path.")
    args = parser.parse_args(argv)

    try:
        summary = build_summary(Path(args.path))
    except Exception as exc:
        summary = {"status": "invalid", "path": args.path, "row_count": 0, "errors": [str(exc)]}

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    if summary["errors"]:
        print(f"Model registry validation failed: {summary['row_count']} row(s), {len(summary['errors'])} error(s).")
        for error in summary["errors"]:
            print(f"- {error}")
        return 1

    print(f"Model registry validation passed: {summary['row_count']} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
