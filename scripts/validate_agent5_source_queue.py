#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.agent5_acquisition import build_source_queue, validate_source_queue


def _rows_from_path(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() in {".yml", ".yaml"}:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    else:
        payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("candidates") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("source queue must be a list or object with candidates list")
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Agent 5 source discovery queue guardrails.")
    parser.add_argument("--path", help="Optional existing source queue JSON/YAML.")
    parser.add_argument("--targets", default="configs/nyse_30_pilot_targets.yml")
    args = parser.parse_args(argv)
    try:
        if args.path:
            rows = _rows_from_path(Path(args.path))
        else:
            payload = yaml.safe_load(Path(args.targets).read_text(encoding="utf-8"))
            rows = build_source_queue(payload.get("targets", []))
        errors = validate_source_queue(rows)
    except Exception as exc:
        rows = []
        errors = [str(exc)]
    if errors:
        print(f"Agent 5 source queue validation failed: {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Agent 5 source queue validation passed: {len(rows)} metadata candidate(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
