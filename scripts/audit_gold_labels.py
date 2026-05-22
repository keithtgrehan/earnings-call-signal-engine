#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.gold_review import audit_gold_labels, write_gold_audit_outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit canonical gold labels without modifying them.")
    parser.add_argument("--path", default="data/gold/gold_labels.jsonl")
    parser.add_argument("--out-dir", default="reports/gold_label_audit")
    args = parser.parse_args(argv)
    summary = audit_gold_labels(Path(args.path))
    write_gold_audit_outputs(summary, Path(args.out_dir))
    print(f"Gold-label audit complete: {summary['valid_count']} valid row(s), canonical gold file unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
