#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = (
    "tool_id",
    "tool_name",
    "category",
    "domain",
    "candidate_use",
    "status",
    "requires_dependency",
    "requires_api_key",
    "requires_model_download",
    "license_check_required",
    "implemented_now",
    "validated_now",
    "notes",
)

VALID_CATEGORIES = {
    "core_nlp",
    "finance_nlp",
    "sales_nlp",
    "support_nlp",
    "account_management_nlp",
    "emotion_detection",
    "embedding",
    "reranker",
    "long_context",
    "evaluation",
    "observability",
}
VALID_DOMAINS = {
    "earnings_calls",
    "sales_calls",
    "customer_support",
    "account_management",
    "general_dialogue",
    "cross_domain",
}
VALID_STATUSES = {"implemented", "candidate", "planned", "blocked", "rejected"}
BOOLEAN_FIELDS = {
    "requires_dependency",
    "requires_api_key",
    "requires_model_download",
    "license_check_required",
    "implemented_now",
    "validated_now",
}


def load_registry(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict) and isinstance(payload.get("tools"), list):
        rows = payload["tools"]
    else:
        raise ValueError("NLP tools registry must be a list or an object with a tools list.")
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError("Every NLP tools registry row must be an object.")
    return rows


def validate_rows(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        for field in REQUIRED_FIELDS:
            if field not in row:
                errors.append(f"row {index}: missing required field {field}")
        tool_id = str(row.get("tool_id", "")).strip()
        if not tool_id:
            errors.append(f"row {index}: tool_id is required")
        elif tool_id in seen:
            errors.append(f"row {index}: duplicate tool_id {tool_id!r}")
        seen.add(tool_id)
        if "category" in row and row["category"] not in VALID_CATEGORIES:
            errors.append(f"row {index}: invalid category {row['category']!r}")
        if "domain" in row and row["domain"] not in VALID_DOMAINS:
            errors.append(f"row {index}: invalid domain {row['domain']!r}")
        if "status" in row and row["status"] not in VALID_STATUSES:
            errors.append(f"row {index}: invalid status {row['status']!r}")
        for field in BOOLEAN_FIELDS:
            if field in row and not isinstance(row[field], bool):
                errors.append(f"row {index}: {field} must be a JSON boolean")
        if row.get("validated_now") is True:
            errors.append(f"row {index}: validated_now must remain false until real benchmark evidence exists")
        if row.get("implemented_now") is True and row.get("status") != "implemented":
            errors.append(f"row {index}: implemented_now true requires status 'implemented'")
    return errors


def build_summary(path: Path) -> dict[str, Any]:
    rows = load_registry(path)
    errors = validate_rows(rows)
    category_counts: dict[str, int] = {}
    for row in rows:
        category = str(row.get("category", ""))
        category_counts[category] = category_counts.get(category, 0) + 1
    return {
        "status": "valid" if not errors else "invalid",
        "path": str(path),
        "row_count": len(rows),
        "category_counts": category_counts,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Signal Engine NLP tools registry JSON file.")
    parser.add_argument("--path", required=True, help="NLP tools registry JSON path.")
    parser.add_argument("--json-out", help="Optional JSON summary output path.")
    args = parser.parse_args(argv)

    try:
        summary = build_summary(Path(args.path))
    except Exception as exc:
        summary = {"status": "invalid", "path": args.path, "row_count": 0, "category_counts": {}, "errors": [str(exc)]}

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    if summary["errors"]:
        print(f"NLP tools registry validation failed: {summary['row_count']} row(s), {len(summary['errors'])} error(s).")
        for error in summary["errors"]:
            print(f"- {error}")
        return 1
    print(f"NLP tools registry validation passed: {summary['row_count']} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
