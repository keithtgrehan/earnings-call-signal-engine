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


def load_registry(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Agent 1 manual-local source registry before deterministic extraction.")
    parser.add_argument("--registry", default="data/review/staging/manual_local_registry.jsonl")
    args = parser.parse_args(argv)
    path = Path(args.registry)
    rows = load_registry(path)
    if not rows:
        print(f"Agent 1 NOT_READY: no registered manual-local transcript sources at {path}.")
        return 0
    errors = validate_manual_local_registry(rows)
    transcript_rows = [row for row in rows if row.get("media_type") == "transcript"]
    if not transcript_rows:
        errors.append("no transcript media_type rows are registered")
    if errors:
        print(f"Agent 1 manual source validation failed: {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Agent 1 manual source validation passed: {len(transcript_rows)} transcript source(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
