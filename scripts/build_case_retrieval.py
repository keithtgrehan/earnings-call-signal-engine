#!/usr/bin/env python3
"""Build a supporting-only retrieval bundle for a demo case."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from earnings_call_sentiment.retrieval_support import (
    DEFAULT_EMBEDDING_BATCH_SIZE,
    DEFAULT_EMBEDDING_DEVICE,
    DEFAULT_EMBEDDING_MAX_LENGTH,
    DEFAULT_EMBEDDING_MODEL,
    build_and_write_case_retrieval_bundle,
    default_case_root,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case-id",
        default="netflix_q1_2022",
        help="Demo case id under data/demo_cases. Default: netflix_q1_2022",
    )
    parser.add_argument(
        "--case-root",
        help="Optional explicit case root. Overrides --case-id when provided.",
    )
    parser.add_argument(
        "--out-dir",
        help="Optional explicit retrieval output directory. Defaults to <case-root>/demo/retrieval.",
    )
    parser.add_argument(
        "--no-embeddings",
        action="store_true",
        help="Skip embedding generation and write a lexical-only retrieval bundle.",
    )
    parser.add_argument(
        "--include-curated-multimodal",
        action="store_true",
        help="Include curated multimodal support rows when available.",
    )
    parser.add_argument(
        "--model-name",
        default=DEFAULT_EMBEDDING_MODEL,
        help=f"Sentence embedding model name. Default: {DEFAULT_EMBEDDING_MODEL}",
    )
    parser.add_argument(
        "--device",
        default=DEFAULT_EMBEDDING_DEVICE,
        help=f"Embedding device: cpu, cuda, or auto. Default: {DEFAULT_EMBEDDING_DEVICE}",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_EMBEDDING_BATCH_SIZE,
        help=f"Embedding batch size. Default: {DEFAULT_EMBEDDING_BATCH_SIZE}",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=DEFAULT_EMBEDDING_MAX_LENGTH,
        help=f"Embedding tokenizer max length. Default: {DEFAULT_EMBEDDING_MAX_LENGTH}",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    case_root = (
        Path(args.case_root).expanduser().resolve()
        if args.case_root
        else default_case_root(args.case_id)
    )
    result = build_and_write_case_retrieval_bundle(
        case_root=case_root,
        out_dir=args.out_dir,
        include_embeddings=not args.no_embeddings,
        include_curated_multimodal=args.include_curated_multimodal,
        model_name=args.model_name,
        device=args.device,
        batch_size=args.batch_size,
        max_length=args.max_length,
    )
    manifest = result["manifest"]
    paths = result["paths"]
    print(f"case_id={manifest['case_id']}")
    print(f"row_count={manifest['row_count']}")
    print(f"source_type_counts={manifest['source_type_counts']}")
    print(f"embedding_status={manifest['embedding']['status']}")
    print(f"embedding_model={manifest['embedding']['model_name']}")
    print(f"rows_path={paths['rows']}")
    print(f"manifest_path={paths['manifest']}")
    print(f"readme_path={paths['readme']}")
    if manifest["embedding"]["status"] == "written":
        print(f"embeddings_path={paths['embeddings']}")
    elif manifest["embedding"]["error"]:
        print(f"embedding_error={manifest['embedding']['error']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
