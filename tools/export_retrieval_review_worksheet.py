#!/usr/bin/env python3
"""Export a metadata-only worksheet for reviewed retrieval query updates."""

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

from signal_engine.retrieval.review_updates import export_review_worksheet  # noqa: E402

DEFAULT_QUERY_SET = ROOT / "data" / "retrieval" / "retrieval_reviewed_query_set.first20.jsonl"
DEFAULT_OBJECTS = ROOT / "data" / "retrieval" / "retrieval_object_metadata.jsonl"
DEFAULT_OUT = ROOT / "reports" / "retrieval" / "retrieval_review_worksheet_first20.csv"


def _repo_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export reviewed retrieval query-set rows to a safe CSV worksheet.")
    parser.add_argument("--query-set", type=Path, default=DEFAULT_QUERY_SET)
    parser.add_argument("--objects", type=Path, default=DEFAULT_OBJECTS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    try:
        summary = export_review_worksheet(
            query_set_path=_repo_path(args.query_set),
            objects_path=_repo_path(args.objects),
            out_path=_repo_path(args.out),
        )
    except Exception as exc:
        print(f"Retrieval review worksheet export blocked: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
