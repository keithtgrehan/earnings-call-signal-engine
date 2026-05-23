#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.ir_sec_acquisition import build_permitted_ingest_queue, read_yaml, write_text, write_yaml


def _load_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = read_yaml(path)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("candidates", "queue", "rows"):
            rows = payload.get(key)
            if isinstance(rows, list):
                return rows
    return []


def build_report(rows: list[dict[str, Any]]) -> str:
    return f"""# IR/SEC Permitted Ingest Queue

Status: no raw acquisition performed.

- Permitted ingest rows: {len(rows)}
- Network used: no
- Raw assets written: no

An empty queue is valid. It means no candidate currently has explicit raw asset permission, checked source terms/robots, and approval/config references.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the IR/SEC permitted ingest queue without acquiring raw assets.")
    parser.add_argument("--policy", default="configs/ir_sec_acquisition_policy.example.yml")
    parser.add_argument("--official-ir", default="data/corpus/official_ir_candidate_map.yml")
    parser.add_argument("--sec-queue", default="data/corpus/sec_metadata_queue.yml")
    parser.add_argument("--out", default="data/corpus/ir_sec_permitted_ingest_queue.yml")
    parser.add_argument("--report", default="reports/agent5/ir_sec_permitted_ingest_queue.md")
    args = parser.parse_args(argv)

    policy = read_yaml(ROOT / args.policy)
    candidates = [*_load_rows(ROOT / args.official_ir), *_load_rows(ROOT / args.sec_queue)]
    rows = build_permitted_ingest_queue(candidates, policy)
    write_yaml(ROOT / args.out, {"status": "valid", "network_used": False, "raw_assets_written": False, "permitted_ingest": rows})
    write_text(ROOT / args.report, build_report(rows))
    print(f"IR/SEC permitted ingest queue written: {len(rows)} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
