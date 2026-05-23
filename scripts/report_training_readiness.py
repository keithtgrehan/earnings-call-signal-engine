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

from signal_engine.gold_review import audit_gold_labels


def _state(valid_gold_count: int, staged_promotions: int) -> str:
    if valid_gold_count >= 100:
        return "TRAINING_READY_CANONICAL"
    if staged_promotions >= 100:
        return "TRAINING_READY_STAGED"
    if staged_promotions > 0:
        return "PROMOTION_READY"
    return "NOT_READY"


def _count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report training readiness state without training.")
    parser.add_argument("--gold", default="data/gold/gold_labels.jsonl")
    parser.add_argument("--promotion-manifest", default="data/review/staging/promotion_manifest.jsonl")
    parser.add_argument("--out-md", default="reports/review/training_readiness.md")
    parser.add_argument("--out-json", default="reports/review/training_readiness.json")
    args = parser.parse_args(argv)
    audit = audit_gold_labels(Path(args.gold))
    valid_count = int(audit.get("valid_count", 0))
    staged = _count_jsonl(Path(args.promotion_manifest))
    state = _state(valid_count, staged)
    payload = {
        "state": state,
        "valid_canonical_gold_count": valid_count,
        "staged_promotion_count": staged,
        "training_attempted": False,
        "minimum_valid_adjudicated_labels": 100,
    }
    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(
        "\n".join(
            [
                "# Training Readiness",
                "",
                f"- State: `{state}`",
                f"- Valid canonical gold count: `{valid_count}`",
                f"- Staged promotion count: `{staged}`",
                "- Training attempted: `false`",
                "- First proof target: `100 valid adjudicated labels`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Training readiness report written with state {state}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
