#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from resource_registry_common import normalize_resource_rows, read_structured, validate_resource_rows, write_json


def build_summary(path: Path) -> dict[str, object]:
    rows = normalize_resource_rows(read_structured(path))
    errors = validate_resource_rows(rows)
    return {
        "status": "valid" if not errors else "invalid",
        "path": str(path),
        "row_count": len(rows),
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate resource registry rights and raw-body guardrails.")
    parser.add_argument("--path", required=True)
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)

    try:
        summary = build_summary(Path(args.path))
    except Exception as exc:
        summary = {"status": "invalid", "path": args.path, "row_count": 0, "errors": [str(exc)]}

    if args.json_out:
        write_json(Path(args.json_out), summary)

    errors = summary["errors"]
    if errors:
        print(f"Resource registry validation failed: {summary['row_count']} row(s), {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Resource registry validation passed: {summary['row_count']} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
