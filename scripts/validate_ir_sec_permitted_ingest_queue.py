#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.ir_sec_acquisition import read_yaml, validate_permitted_ingest_rows


def _rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        rows = payload.get("permitted_ingest", [])
        if isinstance(rows, list):
            return rows
    raise ValueError("permitted ingest queue must be a list or object with permitted_ingest list")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate IR/SEC permitted ingest queue.")
    parser.add_argument("--path", default="data/corpus/ir_sec_permitted_ingest_queue.yml")
    args = parser.parse_args(argv)
    try:
        rows = _rows(read_yaml(ROOT / args.path))
        errors = validate_permitted_ingest_rows(rows)
    except Exception as exc:
        rows = []
        errors = [str(exc)]
    if errors:
        print(f"IR/SEC permitted ingest validation failed: {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"IR/SEC permitted ingest validation passed: {len(rows)} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
