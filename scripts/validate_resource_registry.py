#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from resource_registry_common import normalize_resource_rows, read_structured, validate_resource_rows, write_json


def build_summary(path: Path) -> dict[str, Any]:
    rows = normalize_resource_rows(read_structured(path))
    errors = validate_resource_rows(rows)
    return {
        "status": "valid" if not errors else "invalid",
        "path": str(path),
        "row_count": len(rows),
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Signal Engine source-rights resource registry.")
    parser.add_argument("--path", default="configs/resource_registry.example.yml")
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)

    try:
        summary: dict[str, Any] = build_summary(Path(args.path))
    except Exception as exc:
        summary = {"status": "invalid", "path": args.path, "row_count": 0, "errors": [str(exc)]}

    if args.json_out:
        write_json(Path(args.json_out), summary)

    errors = summary.get("errors", [])
    if errors:
        print(f"Resource registry validation failed: {summary.get('row_count', 0)} row(s), {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Resource registry validation passed: {summary.get('row_count', 0)} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
