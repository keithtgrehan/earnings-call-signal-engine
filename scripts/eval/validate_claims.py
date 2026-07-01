#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.evaluation.claim_gates import validate_claim_language


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate evaluation claim language.")
    parser.add_argument("--path", default="docs/evaluation_claim_language.md")
    args = parser.parse_args(argv)
    path = Path(args.path)
    if not path.exists():
        print(f"Claim language NOT_READY: {path} is missing.")
        return 0
    errors = validate_claim_language(path.read_text(encoding="utf-8"))
    if errors:
        print(f"Evaluation claim validation failed: {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Evaluation claim validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
