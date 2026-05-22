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

from signal_engine.agent5_acquisition import build_500_call_metadata_universe


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a metadata-only 500-call target universe; no raw ingest is performed.")
    parser.add_argument("--count", type=int, default=500)
    parser.add_argument("--out", help="Optional JSON output path. Nothing is written by default.")
    args = parser.parse_args(argv)
    rows = build_500_call_metadata_universe(count=args.count)
    payload = {"status": "metadata_only", "row_count": len(rows), "rows": rows}
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"500-call metadata universe dry-run passed: {len(rows)} target slot(s), no raw ingest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
