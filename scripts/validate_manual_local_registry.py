#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.agent5_acquisition import validate_manual_local_registry


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate manual-local registry path/hash-only records.")
    parser.add_argument("--path", default="data/review/staging/manual_local_registry.jsonl")
    args = parser.parse_args(argv)
    path = Path(args.path)
    if not path.exists():
        print(f"Manual-local registry NOT_READY: {path} is missing. No raw files copied.")
        return 0
    rows = _load_jsonl(path)
    errors = validate_manual_local_registry(rows)
    if errors:
        print(f"Manual-local registry validation failed: {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Manual-local registry validation passed: {len(rows)} path/hash record(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
