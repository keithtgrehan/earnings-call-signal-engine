#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from resource_registry_common import read_structured, write_json

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.media.event_windows import build_event_windows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build sparse transcript-aligned media event-window metadata.")
    parser.add_argument("--path", default="configs/rag_build_policy.example.yml")
    parser.add_argument("--out", help="Optional JSON output path. Nothing is written by default.")
    args = parser.parse_args(argv)
    payload = read_structured(Path(args.path))
    rows = payload.get("synthetic_manifest", []) if isinstance(payload, dict) else []
    windows = build_event_windows(rows)
    if args.out:
        write_json(Path(args.out), {"event_windows": windows})
    print(f"Media event-window dry-run passed: {len(windows)} sparse metadata window(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
