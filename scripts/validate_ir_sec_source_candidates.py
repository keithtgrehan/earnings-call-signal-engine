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

from signal_engine.ir_sec_acquisition import read_yaml, validate_source_candidates


def _rows(path: Path) -> list[dict[str, Any]]:
    payload = read_yaml(path)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("candidates", "queue", "rows"):
            rows = payload.get(key)
            if isinstance(rows, list):
                return rows
    raise ValueError(f"{path} must contain a list or candidates/queue rows")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate IR/SEC source candidate rows.")
    parser.add_argument(
        "--path",
        action="append",
        default=[],
        help="Candidate YAML path. May be supplied more than once.",
    )
    args = parser.parse_args(argv)
    paths = args.path or ["data/corpus/official_ir_candidate_map.yml", "data/corpus/sec_metadata_queue.yml"]
    errors: list[str] = []
    row_count = 0
    for path_value in paths:
        path = ROOT / path_value
        try:
            rows = _rows(path)
            row_count += len(rows)
            errors.extend(f"{path_value}: {error}" for error in validate_source_candidates(rows))
        except Exception as exc:
            errors.append(f"{path_value}: {exc}")
    if errors:
        print(f"IR/SEC source candidate validation failed: {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"IR/SEC source candidate validation passed: {row_count} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
