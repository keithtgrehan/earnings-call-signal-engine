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

from resource_registry_common import write_json
from validate_training_plan import build_summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report gated training readiness without training by default.")
    parser.add_argument("--plan", default="configs/training_plan.example.yml")
    parser.add_argument("--allow-train", action="store_true", help="Require all gates to be READY before any non-smoke training path.")
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)

    summary = build_summary(Path(args.plan))
    summary["mode"] = "readiness_only"
    summary["training_attempted"] = False
    if args.allow_train and summary["status"] != "ready":
        summary["allow_train_result"] = "refused"
        summary["reason"] = "Training refused because readiness gates are not ready."
    elif args.allow_train:
        summary["allow_train_result"] = "ready_but_not_executed"
        summary["reason"] = "Production training execution is outside this scaffold; use a reviewed training runner later."
    else:
        summary["allow_train_result"] = "not_requested"

    if args.json_out:
        write_json(Path(args.json_out), summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] != "invalid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
