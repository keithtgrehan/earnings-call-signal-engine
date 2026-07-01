#!/usr/bin/env python3
"""Validate sanitized long-context reviewer-output candidates."""

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

from signal_engine.retrieval.long_context_review_output import (  # noqa: E402
    batch_validate_long_context_review_outputs,
    validate_long_context_review_output_file,
)


def _repo_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate gated long-context reviewer-output candidates.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--review-output", type=Path, help="Validate one JSON/JSONL reviewer-output candidate.")
    mode.add_argument("--all-samples", type=Path, help="Validate all safe sample reviewer-output files in a directory.")
    parser.add_argument("--prompt-pack", type=Path)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--prompt-pack-dir", type=Path)
    parser.add_argument("--bundle-dir", type=Path)
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args(argv)

    try:
        if args.review_output is not None:
            if args.prompt_pack is None or args.bundle is None:
                raise ValueError("--review-output requires --prompt-pack and --bundle")
            summary = validate_long_context_review_output_file(
                review_output_path=_repo_path(args.review_output),
                prompt_pack_path=_repo_path(args.prompt_pack),
                bundle_path=_repo_path(args.bundle),
                out_path=_repo_path(args.out) if args.out else None,
                json_out_path=_repo_path(args.json_out) if args.json_out else None,
            )
        else:
            assert args.all_samples is not None
            if args.prompt_pack_dir is None or args.bundle_dir is None or args.out_dir is None:
                raise ValueError("--all-samples requires --prompt-pack-dir, --bundle-dir, and --out-dir")
            summary = batch_validate_long_context_review_outputs(
                samples_dir=_repo_path(args.all_samples),
                prompt_pack_dir=_repo_path(args.prompt_pack_dir),
                bundle_dir=_repo_path(args.bundle_dir),
                out_dir=_repo_path(args.out_dir),
            )
    except Exception as exc:
        print(f"Long-context review-output validation blocked: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
