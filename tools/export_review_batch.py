#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import shutil


def main() -> int:
    parser = argparse.ArgumentParser(description="Export the minimal active-learning review batch.")
    parser.add_argument("--input", default="data/processed/multimodal_engine/next_review_batch.csv")
    parser.add_argument("--output", default="outputs/next_review_batch.csv")
    args = parser.parse_args()
    source = Path(args.input)
    target = Path(args.output)
    if not source.exists():
        raise SystemExit(f"review batch not found: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    print(f"exported {source} -> {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
