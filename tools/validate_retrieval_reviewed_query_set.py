#!/usr/bin/env python3
"""Validate metadata-only reviewed retrieval query-set rows."""

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

from signal_engine.retrieval.reviewed_query_set import validate_and_summarize_reviewed_query_set  # noqa: E402

DEFAULT_QUERY_SET = ROOT / "data" / "retrieval" / "retrieval_reviewed_query_set.template.jsonl"
DEFAULT_OBJECTS = ROOT / "data" / "retrieval" / "retrieval_object_metadata.jsonl"


def validate_retrieval_reviewed_query_set(
    *,
    query_set_path: Path = DEFAULT_QUERY_SET,
    objects_path: Path = DEFAULT_OBJECTS,
    allow_template: bool = False,
) -> dict[str, object]:
    query_file = query_set_path if query_set_path.is_absolute() else ROOT / query_set_path
    objects_file = objects_path if objects_path.is_absolute() else ROOT / objects_path
    return validate_and_summarize_reviewed_query_set(
        query_set_path=query_file,
        objects_path=objects_file,
        allow_template=allow_template,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a reviewed retrieval query-set JSONL file.")
    parser.add_argument("--query-set", type=Path, default=DEFAULT_QUERY_SET)
    parser.add_argument("--objects", type=Path, default=DEFAULT_OBJECTS)
    parser.add_argument("--allow-template", action="store_true", help="Allow template_only rows for scaffold planning.")
    args = parser.parse_args(argv)
    try:
        summary = validate_retrieval_reviewed_query_set(
            query_set_path=args.query_set,
            objects_path=args.objects,
            allow_template=args.allow_template,
        )
    except Exception as exc:
        print(f"Reviewed retrieval query-set validation blocked: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
