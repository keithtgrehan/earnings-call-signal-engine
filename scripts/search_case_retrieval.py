#!/usr/bin/env python3
"""Search a supporting-only case retrieval bundle."""

from __future__ import annotations

import argparse
from pathlib import Path

from earnings_call_sentiment.retrieval_support import (
    DEFAULT_EMBEDDING_DEVICE,
    default_bundle_dir,
    default_case_root,
    load_retrieval_bundle,
    _normalize_space,
    search_retrieval_rows,
)


def _excerpt(text: str, max_chars: int = 220) -> str:
    normalized = " ".join(str(text or "").split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 3].rstrip() + "..."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "query",
        nargs="?",
        help="Free-text query for the retrieval bundle.",
    )
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
        "--bundle-dir",
        help="Optional retrieval bundle directory. Defaults to <case-root>/demo/retrieval.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=8,
        help="Number of results to print. Default: 8",
    )
    parser.add_argument(
        "--mode",
        default="hybrid",
        choices=("lexical", "semantic", "hybrid"),
        help="Retrieval mode. Default: hybrid",
    )
    parser.add_argument(
        "--device",
        default=DEFAULT_EMBEDDING_DEVICE,
        help=f"Embedding device for semantic queries: cpu, cuda, or auto. Default: {DEFAULT_EMBEDDING_DEVICE}",
    )
    parser.add_argument(
        "--like-row-id",
        help="Reuse an existing retrieval row as the semantic query seed.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.query and not args.like_row_id:
        raise SystemExit("Provide either a free-text query or --like-row-id.")
    case_root = (
        Path(args.case_root).expanduser().resolve()
        if args.case_root
        else default_case_root(args.case_id)
    )
    bundle_dir = (
        Path(args.bundle_dir).expanduser().resolve()
        if args.bundle_dir
        else default_bundle_dir(case_root)
    )
    bundle = load_retrieval_bundle(bundle_dir)
    manifest = bundle.manifest
    model_name = manifest.get("embedding", {}).get("model_name")
    query_text = args.query or ""
    query_embedding = None
    exclude_row_ids: set[str] | None = None
    if args.like_row_id:
        matching_index = next(
            (
                index
                for index, row in enumerate(bundle.rows)
                if str(row.get("row_id")) == args.like_row_id
            ),
            None,
        )
        if matching_index is None:
            raise SystemExit(f"Could not find row_id '{args.like_row_id}' in the retrieval bundle.")
        seed_row = bundle.rows[matching_index]
        query_text = str(seed_row.get("text", ""))
        seed_text = _normalize_space(seed_row.get("text"))
        exclude_row_ids = {
            str(row.get("row_id"))
            for row in bundle.rows
            if _normalize_space(row.get("text")) == seed_text
        }
        if bundle.embeddings is not None:
            query_embedding = bundle.embeddings[matching_index]
    results, notes = search_retrieval_rows(
        query=query_text,
        rows=bundle.rows,
        top_k=args.top_k,
        mode=args.mode,
        row_embeddings=bundle.embeddings,
        query_embedding=query_embedding,
        model_name=model_name,
        device=args.device,
        exclude_row_ids=exclude_row_ids,
    )

    print("Supporting-only retrieval output. Deterministic transcript-backed artifacts remain canonical.")
    print(f"case_id={manifest['case_id']}")
    print(f"requested_mode={args.mode}")
    if args.like_row_id:
        print(f"seed_row_id={args.like_row_id}")
    if notes:
        for note in notes:
            print(f"note={note}")
    if not results:
        print("No matching retrieval rows were found.")
        return 0

    for result in results:
        row = result.row
        label = row.get("plain_english_label") or row.get("deterministic_category") or ""
        print()
        print(f"rank={result.rank} score={result.score:.4f} mode={result.retrieval_mode}")
        print(f"row_id={row['row_id']}")
        print(f"source_type={row['source_type']} case_id={row['case_id']}")
        if label:
            print(f"label={label}")
        if row.get("deterministic_category"):
            print(f"deterministic_category={row['deterministic_category']}")
        print(f"source_locator={row['source_locator']}")
        print(f"supporting_only={row['supporting_only']}")
        print(f"text={_excerpt(str(row.get('text', '')))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
