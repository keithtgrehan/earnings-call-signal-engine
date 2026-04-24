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

from signal_engine.domains import SUPPORTED_DOMAINS
from signal_engine.pipeline import analyze_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run deterministic Signal Engine 2.0 analysis on a transcript JSON or JSONL file."
    )
    parser.add_argument("input_path", help="Path to a JSON or JSONL transcript file.")
    parser.add_argument(
        "--domain",
        required=True,
        choices=SUPPORTED_DOMAINS,
        help="Conversation domain to analyze.",
    )
    parser.add_argument(
        "--conversation-id",
        help="Optional conversation id to select when the input file contains multiple records.",
    )
    args = parser.parse_args(argv)

    results = analyze_path(args.input_path, domain=args.domain)
    if not results:
        raise RuntimeError("No analyzable conversations found.")

    if args.conversation_id:
        matches = [item for item in results if item["conversation_id"] == args.conversation_id]
        if not matches:
            raise RuntimeError(f"Conversation id not found: {args.conversation_id}")
        payload = matches[0]
    else:
        payload = results[0]

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
