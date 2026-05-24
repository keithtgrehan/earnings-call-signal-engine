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

from signal_engine.evaluation.claim_gates import claim_disclaimers
from signal_engine.evaluation.control_readiness import control_readiness
from signal_engine.evaluation.estimation_window import estimation_window_readiness
from signal_engine.evaluation.event_windows import supported_event_windows
from signal_engine.evaluation.sample_gates import evaluate_sample_gates


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build evaluation gate report with explicit no-claim boundaries.")
    parser.add_argument("--valid-gold-count", type=int, default=0)
    parser.add_argument("--call-count", type=int, default=30)
    parser.add_argument("--out-json", default="reports/evaluation/evaluation_gate_report.json")
    parser.add_argument("--out-md", default="reports/evaluation/evaluation_gate_report.md")
    args = parser.parse_args(argv)
    payload = {
        "sample_gates": evaluate_sample_gates(valid_gold_count=args.valid_gold_count, call_count=args.call_count),
        "event_windows": supported_event_windows(),
        "estimation_window": estimation_window_readiness(prior_trading_days=None, market_data_available=False),
        "control_readiness": control_readiness(),
        "claim_disclaimers": claim_disclaimers(),
    }
    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Evaluation Gate Report",
        "",
        "- 30-call pilot: pipeline readiness only.",
        "- 100 valid adjudicated labels required before signal extraction evaluation readiness.",
        "- 100-150 calls required before retrieval benchmark readiness.",
        "- 500-call universe remains metadata/readiness map only.",
        "",
        "## Claim Boundaries",
        "",
        *[f"- `{item}`" for item in payload["claim_disclaimers"]],
    ]
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Evaluation gate report written to {out_json} and {out_md}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
