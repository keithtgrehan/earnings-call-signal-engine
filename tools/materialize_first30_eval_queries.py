#!/usr/bin/env python3
"""Materialize first30 retrieval eval queries from current retrieval objects."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evaluate_retrieval import DEFAULT_OBJECTS, MATERIALIZED_FIRST30_QUERIES, materialize_first30_queries


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize first30 retrieval eval queries.")
    parser.add_argument("--objects", type=Path, default=DEFAULT_OBJECTS)
    parser.add_argument("--out", type=Path, default=MATERIALIZED_FIRST30_QUERIES)
    args = parser.parse_args(argv)
    rows = materialize_first30_queries(args.objects, args.out)
    print(json.dumps({"query_count": len(rows), "out": str(args.out), "raw_text_returned": False}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
