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
        description="Analyze a single conversation from a JSON or JSONL file."
    )
    parser.add_argument("input_path", help="Path to a JSON or JSONL input file.")
    parser.add_argument(
        "--conversation-id",
        help="Optional conversation id to select when the input contains multiple conversations.",
    )
    args = parser.parse_args(argv)

    results = analyze_file(args.input_path)
    if not results:
        raise RuntimeError("No conversations found in the input file.")

    if args.conversation_id:
        matches = [row for row in results if row["conversation_id"] == args.conversation_id]
        if not matches:
            raise RuntimeError(f"Conversation id not found: {args.conversation_id}")
        output = matches[0]
    else:
        output = results[0]

    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
