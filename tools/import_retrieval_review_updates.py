#!/usr/bin/env python3
"""Import safe reviewer updates into a reviewed retrieval query-set candidate."""

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

from signal_engine.retrieval.review_updates import import_review_updates  # noqa: E402

DEFAULT_QUERY_SET = ROOT / "data" / "retrieval" / "retrieval_reviewed_query_set.first20.jsonl"
DEFAULT_OBJECTS = ROOT / "data" / "retrieval" / "retrieval_object_metadata.jsonl"
DEFAULT_UPDATES = ROOT / "reports" / "retrieval" / "retrieval_review_worksheet_first20.csv"
DEFAULT_OUT = ROOT / "data" / "retrieval" / "retrieval_reviewed_query_set.first20.reviewed_candidate.jsonl"
DEFAULT_SUMMARY_JSON = ROOT / "reports" / "retrieval" / "retrieval_review_import_summary.json"
DEFAULT_SUMMARY_MD = ROOT / "reports" / "retrieval" / "retrieval_review_import_summary.md"


def _repo_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import safe reviewer updates into a candidate query-set JSONL file.")
    parser.add_argument("--query-set", type=Path, default=DEFAULT_QUERY_SET)
    parser.add_argument("--review-updates", type=Path, default=DEFAULT_UPDATES)
    parser.add_argument("--objects", type=Path, default=DEFAULT_OBJECTS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--summary-md", type=Path, default=DEFAULT_SUMMARY_MD)
    args = parser.parse_args(argv)
    try:
        summary = import_review_updates(
            query_set_path=_repo_path(args.query_set),
            review_updates_path=_repo_path(args.review_updates),
            objects_path=_repo_path(args.objects),
            out_path=_repo_path(args.out),
            summary_json_path=_repo_path(args.summary_json),
            summary_md_path=_repo_path(args.summary_md),
        )
    except Exception as exc:
        print(f"Retrieval review update import blocked: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
