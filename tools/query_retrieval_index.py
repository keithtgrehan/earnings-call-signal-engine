#!/usr/bin/env python3
"""Query the local metadata-only retrieval index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.retrieval.query import query_local_index

DEFAULT_INDEX = ROOT / ".local" / "signal_engine" / "retrieval" / "indexes" / "nyse100_bm25"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Query local metadata-only retrieval index.")
    parser.add_argument("query")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args(argv)
    print(json.dumps(query_local_index(args.index, args.query, limit=args.limit), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
