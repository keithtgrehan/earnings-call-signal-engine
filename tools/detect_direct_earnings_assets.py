#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.acquisition.asset_resolver import RESOLVED_ASSET_FIELDS, read_csv, write_csv, write_resolution_report
from signal_engine.acquisition.direct_asset_detector import detect_direct_asset

DEFAULT_IN = ROOT / "data" / "acquisition" / "nyse_100_resolved_asset_candidates.csv"
DEFAULT_OUT = ROOT / "data" / "acquisition" / "nyse_100_direct_asset_detection.csv"
DEFAULT_REPORT = ROOT / "reports" / "acquisition" / "direct_asset_detection.md"


def run(in_path: Path, out: Path, report: Path) -> dict[str, int]:
    rows = read_csv(in_path)
    direct_like = [row for row in rows if row.get("download_allowed") == "true"]
    detected = [detect_direct_asset(row) for row in direct_like]
    write_csv(out, detected, RESOLVED_ASSET_FIELDS)
    write_resolution_report(report, detected, title="Direct Asset Detection")
    return {"input_rows": len(rows), "detected_rows": len(detected)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Confirm direct transcript/audio asset candidates.")
    parser.add_argument("--in", dest="in_path", type=Path, default=DEFAULT_IN)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    print(json.dumps(run(args.in_path, args.out, args.report), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
