#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pipeline import analyze_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Batch-build deterministic QA/risk rows from JSON or JSONL conversations."
    )
    parser.add_argument("input_path", help="Path to a JSON or JSONL input file.")
    parser.add_argument(
        "--output",
        help="Optional output path. Uses JSON for .json and JSONL for .jsonl.",
    )
    args = parser.parse_args(argv)

    results = analyze_file(args.input_path)
    if args.output:
        output_path = Path(args.output)
        if output_path.suffix.lower() == ".jsonl":
            lines = [json.dumps(row, ensure_ascii=False) for row in results]
            output_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        else:
            output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
