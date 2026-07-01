#!/usr/bin/env python3
"""Build or validate gated long-context prompt packs from case bundles."""

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

from signal_engine.retrieval.long_context_prompt_pack import (  # noqa: E402
    build_all_long_context_prompt_packs,
    build_long_context_prompt_pack,
    validate_long_context_prompt_pack_file,
)

DEFAULT_OUT_DIR = ROOT / "reports" / "long_context"


def _repo_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def _case_id_from_bundle_name(path: Path) -> str:
    name = path.name
    return name.removesuffix(".case_review_bundle.json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build gated long-context prompt packs.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--bundle", type=Path, help="Build one prompt pack from a case bundle JSON.")
    mode.add_argument("--all-bundles", type=Path, help="Build one prompt pack per case bundle in a directory.")
    mode.add_argument("--validate", type=Path, help="Validate a prompt pack JSON or prompt-pack index JSON.")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)

    try:
        if args.validate is not None:
            summary = validate_long_context_prompt_pack_file(_repo_path(args.validate))
        elif args.all_bundles is not None:
            summary = build_all_long_context_prompt_packs(
                bundles_dir=_repo_path(args.all_bundles),
                out_dir=_repo_path(args.out_dir),
            )
        else:
            assert args.bundle is not None
            bundle_path = _repo_path(args.bundle)
            case_id = _case_id_from_bundle_name(bundle_path)
            out_path = _repo_path(args.out) if args.out else DEFAULT_OUT_DIR / f"{case_id}.prompt_pack.json"
            report_path = _repo_path(args.report) if args.report else DEFAULT_OUT_DIR / f"{case_id}.prompt_pack.md"
            summary = build_long_context_prompt_pack(
                bundle_path=bundle_path,
                out_path=out_path,
                report_path=report_path,
            )
    except Exception as exc:
        print(f"Long-context prompt-pack command blocked: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
