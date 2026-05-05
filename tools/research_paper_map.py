#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.research.paper_metadata import VALID_CATEGORIES, filter_by_category, get_paper, load_papers

MATRIX_PATH = ROOT / "data" / "research" / "ilya_reading_list" / "research_to_signal_engine_matrix.csv"


def _print_paper(paper: dict[str, Any]) -> None:
    print(f"{paper['title']} ({paper.get('year', 'unknown')})")
    print(f"ID: {paper['id']}")
    print(f"Authors: {', '.join(paper.get('authors', []))}")
    print(f"Category: {paper['category']}")
    print(f"Status: {paper['implementation_status']} | Confidence: {paper['confidence']}")
    print(f"Core idea: {paper.get('core_idea', '')}")
    print("Signal Engine relevance:")
    for item in paper.get("signal_engine_relevance", []):
        print(f"- {item}")
    print("Future feature ideas:")
    for item in paper.get("future_features", []):
        print(f"- {item}")
    print("Sources:")
    for url in paper.get("source_urls", []):
        print(f"- {url}")


def _list_papers() -> None:
    for paper in load_papers():
        print(f"{paper['id']}\t{paper['title']}\t{paper['category']}\t{paper['implementation_status']}")


def _print_category(category: str) -> None:
    for paper in filter_by_category(category):
        print(f"{paper['id']}: {paper['title']}")
        for relevance in paper.get("signal_engine_relevance", [])[:2]:
            print(f"  - {relevance}")


def _signal_engine_roadmap() -> None:
    with MATRIX_PATH.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    print("Signal Engine 2.0 Research Roadmap Inputs")
    print("Now:")
    for row in rows:
        if row["category"] in {"attention_transformers", "sequence_models", "compression_mdl_complexity", "evaluation_theory"}:
            print(f"- {row['title']}: {row['future_ai_tools']}")
    print("Later:")
    for row in rows:
        if row["category"] in {"speech_audio", "vision_multimodal", "graph_relational_learning", "reasoning_memory", "scaling_systems"}:
            print(f"- {row['title']}: {row['future_ai_tools']}")


def _export_markdown() -> None:
    print("# Ilya Reading List Paper Map\n")
    for paper in load_papers():
        print(f"## {paper['title']}")
        print("")
        print(f"- ID: `{paper['id']}`")
        print(f"- Category: `{paper['category']}`")
        print(f"- Status: `{paper['implementation_status']}`")
        print(f"- Confidence: `{paper['confidence']}`")
        print(f"- Core idea: {paper.get('core_idea', '')}")
        print("- Signal Engine relevance:")
        for item in paper.get("signal_engine_relevance", []):
            print(f"  - {item}")
        print("")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Explore Ilya reading-list research metadata for Signal Engine 2.0.")
    parser.add_argument("--list", action="store_true", help="List all papers.")
    parser.add_argument("--paper", help="Show one paper by id.")
    parser.add_argument("--category", choices=sorted(VALID_CATEGORIES), help="Show papers in a category.")
    parser.add_argument("--signal-engine-roadmap", action="store_true", help="Print roadmap-oriented paper mappings.")
    parser.add_argument("--export-markdown", action="store_true", help="Print a Markdown paper map.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    selected = [args.list, bool(args.paper), bool(args.category), args.signal_engine_roadmap, args.export_markdown]
    if sum(selected) != 1:
        parser.error("Choose exactly one action.")

    if args.list:
        _list_papers()
    elif args.paper:
        _print_paper(get_paper(args.paper))
    elif args.category:
        _print_category(args.category)
    elif args.signal_engine_roadmap:
        _signal_engine_roadmap()
    elif args.export_markdown:
        _export_markdown()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
