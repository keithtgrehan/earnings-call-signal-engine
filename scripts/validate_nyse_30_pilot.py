#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.agent5_acquisition import validate_nyse_30_targets


def _rows(payload: Any) -> list[dict[str, Any]]:
    rows = payload.get("targets") if isinstance(payload, dict) else payload
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("NYSE 30 pilot config must be a list or object with targets list.")
    return rows


def build_summary(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    rows = _rows(payload)
    errors = validate_nyse_30_targets(rows)
    return {"status": "valid" if not errors else "invalid", "row_count": len(rows), "errors": errors}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the rights-safe NYSE 30 pilot target queue.")
    parser.add_argument("--path", default="configs/nyse_30_pilot_targets.yml")
    args = parser.parse_args(argv)
    try:
        summary = build_summary(Path(args.path))
    except Exception as exc:
        summary = {"status": "invalid", "row_count": 0, "errors": [str(exc)]}
    if summary["errors"]:
        print(f"NYSE 30 pilot validation failed: {len(summary['errors'])} error(s).")
        for error in summary["errors"]:
            print(f"- {error}")
        return 1
    print(f"NYSE 30 pilot validation passed: {summary['row_count']} metadata-only target(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
