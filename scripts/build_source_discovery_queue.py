#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from resource_registry_common import read_structured, write_json
from validate_source_discovery_queue import build_summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build source discovery queue metadata without downloading content.")
    parser.add_argument("--path", default="configs/source_discovery_policy.example.yml")
    parser.add_argument("--out", help="Optional JSON output. Nothing is written by default.")
    args = parser.parse_args(argv)
    summary = build_summary(Path(args.path))
    payload = read_structured(Path(args.path))
    if args.out:
        write_json(Path(args.out), {"summary": summary, "candidates": payload.get("candidates", [])})
    if summary["errors"]:
        print("Source discovery queue build blocked by validation errors.")
        return 1
    print(f"Source discovery queue dry-run passed: {summary['row_count']} metadata candidate(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
