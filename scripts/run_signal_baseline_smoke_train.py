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
from signal_engine.training import output_path_is_tmp, synthetic_smoke_metrics


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a synthetic-only baseline smoke check; no model weights are written.")
    parser.add_argument("--allow-train", action="store_true", help="Required to run the synthetic smoke path.")
    parser.add_argument("--out", default="/tmp/signal_engine_smoke_training/baseline_smoke_metrics.json")
    args = parser.parse_args(argv)

    out_path = Path(args.out)
    if not args.allow_train:
        payload = {
            "status": "dry_run",
            "training_attempted": False,
            "reason": "Pass --allow-train to run synthetic smoke training only.",
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    if not output_path_is_tmp(out_path):
        print("Synthetic smoke output must be under /tmp; refusing to write tracked repo artifacts.", file=sys.stderr)
        return 2
    payload = synthetic_smoke_metrics()
    payload["training_attempted"] = True
    payload["output_path"] = str(out_path)
    write_json(out_path, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
