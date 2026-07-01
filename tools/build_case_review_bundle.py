#!/usr/bin/env python3
"""Build or validate metadata-only case review bundles."""

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

from signal_engine.retrieval.case_bundle import (  # noqa: E402
    build_all_case_review_bundles,
    build_case_review_bundle,
    normalize_case_id,
    validate_case_review_bundle_file,
)

DEFAULT_OBJECTS = ROOT / "data" / "retrieval" / "retrieval_object_metadata.jsonl"
DEFAULT_QUERY_SET = ROOT / "data" / "retrieval" / "retrieval_reviewed_query_set.first20.jsonl"
DEFAULT_OUT_DIR = ROOT / "reports" / "case_bundles"


def _repo_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def _default_bundle_json(case_id: str) -> Path:
    return DEFAULT_OUT_DIR / f"{normalize_case_id(case_id)}.case_review_bundle.json"


def _default_bundle_md(case_id: str) -> Path:
    return DEFAULT_OUT_DIR / f"{normalize_case_id(case_id)}.case_review_bundle.md"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build metadata-only case review bundles.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--case-id", help="Build one case bundle for the given case ID.")
    mode.add_argument("--all-cases", action="store_true", help="Build one case bundle per retrieval-object case.")
    mode.add_argument("--validate", type=Path, help="Validate a case bundle JSON or bundle index JSON.")
    parser.add_argument("--objects", type=Path, default=DEFAULT_OBJECTS)
    parser.add_argument("--query-set", type=Path, default=DEFAULT_QUERY_SET)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)

    try:
        if args.validate is not None:
            summary = validate_case_review_bundle_file(_repo_path(args.validate))
        elif args.all_cases:
            summary = build_all_case_review_bundles(
                objects_path=_repo_path(args.objects),
                query_set_path=_repo_path(args.query_set),
                out_dir=_repo_path(args.out_dir),
            )
        else:
            assert args.case_id is not None
            summary = build_case_review_bundle(
                case_id=args.case_id,
                objects_path=_repo_path(args.objects),
                query_set_path=_repo_path(args.query_set),
                out_path=_repo_path(args.out) if args.out else _default_bundle_json(args.case_id),
                report_path=_repo_path(args.report) if args.report else _default_bundle_md(args.case_id),
            )
    except Exception as exc:
        print(f"Case review bundle command blocked: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
