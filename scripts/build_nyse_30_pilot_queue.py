#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.agent5_acquisition import build_nyse_30_targets, validate_nyse_30_targets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the metadata-only NYSE 30 pilot target queue.")
    parser.add_argument("--out", help="Optional YAML output path. Nothing is written by default.")
    args = parser.parse_args(argv)
    targets = build_nyse_30_targets()
    errors = validate_nyse_30_targets(targets)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(yaml.safe_dump({"targets": targets}, sort_keys=False), encoding="utf-8")
    if errors:
        print(f"NYSE 30 pilot build blocked: {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"NYSE 30 pilot build dry-run passed: {len(targets)} metadata-only target(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
