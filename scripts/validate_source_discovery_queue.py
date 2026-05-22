#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

from resource_registry_common import read_structured, write_json

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.data_sources.discovery_queue import validate_candidate


def _rows(payload: Any) -> list[dict[str, Any]]:
    rows = payload.get("candidates") if isinstance(payload, dict) else payload
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("Discovery queue must be a list or object with candidates list.")
    return rows


def build_summary(path: Path) -> dict[str, Any]:
    rows = _rows(read_structured(path))
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        for error in validate_candidate(row):
            errors.append(f"row {index}: {error}")
    return {"status": "valid" if not errors else "invalid", "row_count": len(rows), "errors": errors}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate metadata-only source discovery queue.")
    parser.add_argument("--path", default="configs/source_discovery_policy.example.yml")
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)
    try:
        summary = build_summary(Path(args.path))
    except Exception as exc:
        summary = {"status": "invalid", "row_count": 0, "errors": [str(exc)]}
    if args.json_out:
        write_json(Path(args.json_out), summary)
    if summary["errors"]:
        print(f"Source discovery validation failed: {len(summary['errors'])} error(s).")
        for error in summary["errors"]:
            print(f"- {error}")
        return 1
    print(f"Source discovery validation passed: {summary['row_count']} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
