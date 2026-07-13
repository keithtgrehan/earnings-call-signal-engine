#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.control_room.status import build_control_room_status, write_control_room_outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build fail-closed Control Room status from readiness reports.")
    parser.add_argument("--readiness-json", default="reports/readiness_canonical.json")
    parser.add_argument("--repair-manifest", default="data/review/staging/legacy_gold_repair_manifest.jsonl")
    parser.add_argument("--json-out", default="reports/control_room/status.json")
    parser.add_argument("--md-out", default="reports/control_room/status.md")
    args = parser.parse_args(argv)

    status = build_control_room_status(
        readiness_json=Path(args.readiness_json),
        repair_manifest=Path(args.repair_manifest),
    )
    write_control_room_outputs(status, json_out=Path(args.json_out), md_out=Path(args.md_out))
    print(
        "Control Room status "
        f"{status['status']}: training {status['training']['status']} with "
        f"{status['strict_valid_gold_count']}/"
        f"{status['minimum_strict_valid_gold_labels']} strict-valid gold rows."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
