#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.agent5_acquisition import build_source_queue, validate_source_queue


def _load_targets(path: Path) -> list[dict[str, object]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    rows = payload.get("targets") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("target config must contain a targets list")
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Agent 5 source discovery queue metadata without downloading source bodies.")
    parser.add_argument("--targets", default="configs/nyse_30_pilot_targets.yml")
    parser.add_argument("--out", help="Optional JSON output path. Nothing is written by default.")
    args = parser.parse_args(argv)
    rows = build_source_queue(_load_targets(Path(args.targets)))
    errors = validate_source_queue(rows)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"status": "valid" if not errors else "invalid", "row_count": len(rows), "candidates": rows}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if errors:
        print(f"Agent 5 source queue build blocked: {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Agent 5 source queue build dry-run passed: {len(rows)} metadata candidate(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
