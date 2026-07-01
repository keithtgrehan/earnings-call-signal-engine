#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.evaluation.sample_gates import evaluate_sample_gates


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run sample-size evaluation gates.")
    parser.add_argument("--valid-gold-count", type=int, default=0)
    parser.add_argument("--call-count", type=int, default=30)
    parser.add_argument("--out", default="reports/evaluation/sample_gates.json")
    args = parser.parse_args(argv)
    payload = evaluate_sample_gates(valid_gold_count=args.valid_gold_count, call_count=args.call_count)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Sample gates written to {out}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
