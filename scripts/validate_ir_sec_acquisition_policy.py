#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.ir_sec_acquisition import read_yaml, validate_policy


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate IR/SEC acquisition policy guardrails.")
    parser.add_argument("--path", default="configs/ir_sec_acquisition_policy.example.yml")
    args = parser.parse_args(argv)
    try:
        errors = validate_policy(read_yaml(ROOT / args.path))
    except Exception as exc:
        errors = [str(exc)]
    if errors:
        print(f"IR/SEC acquisition policy validation failed: {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    print("IR/SEC acquisition policy validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
