#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.research.paper_metadata import VALID_CATEGORIES, filter_by_category, get_paper, load_papers

MATRIX_PATH = ROOT / "data" / "research" / "ilya_reading_list" / "research_to_signal_engine_matrix.csv"
SOURCE_REGISTRY_PATH = ROOT / "data" / "research" / "ilya_reading_list" / "source_registry.json"
FEATURE_BACKLOG_PATH = ROOT / "data" / "research" / "ilya_reading_list" / "signal_engine_feature_backlog.csv"
READING_PLAN_PATH = ROOT / "docs" / "research" / "ilya_reading_list" / "keith_reading_plan.md"
PAPER_BRIEF_DIR = ROOT / "docs" / "research" / "ilya_reading_list" / "papers"
VALIDATE_SCRIPT = ROOT / "tools" / "research_sources" / "validate_research_asset.py"


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


def _brief_path(paper_id: str) -> Path:
    matches = sorted(PAPER_BRIEF_DIR.glob(f"*_{paper_id}.md"))
    if not matches and paper_id == "stanford_cs231n_convolutional_neural_networks":
        matches = [PAPER_BRIEF_DIR / "26_cs231n.md"]
    if not matches:
        raise SystemExit(f"No brief found for paper id: {paper_id}")
    return matches[0]


def _print_brief(paper_id: str) -> None:
    get_paper(paper_id)
    print(_brief_path(paper_id).read_text(encoding="utf-8"))


def _parsed_status() -> None:
    registry = json.loads(SOURCE_REGISTRY_PATH.read_text(encoding="utf-8"))
    counts: dict[str, int] = {}
    for entry in registry:
        status = entry["parse_status"]
        counts[status] = counts.get(status, 0) + 1
        print(f"{entry['id']}\t{status}\t{entry.get('source_type')}\t{entry.get('canonical_url')}")
    print("Summary:")
    for status, count in sorted(counts.items()):
        print(f"- {status}: {count}")


def _feature_backlog() -> None:
    with FEATURE_BACKLOG_PATH.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    for row in rows:
        print(f"{row['feature_id']}: {row['feature_name']}")
        print(f"  area={row['signal_engine_area']} stage={row['implementation_stage']} value={row['expected_value']}")
        print(f"  eval={row['evaluation_method']}")


def _reading_plan() -> None:
    print(READING_PLAN_PATH.read_text(encoding="utf-8"))


def _source_registry() -> None:
    registry = json.loads(SOURCE_REGISTRY_PATH.read_text(encoding="utf-8"))
    for entry in registry:
        print(f"{entry['id']}: {entry['parse_status']} | download_allowed={entry['download_allowed']} | {entry.get('canonical_url')}")


def _validate_full_asset() -> None:
    subprocess.run([sys.executable, str(VALIDATE_SCRIPT)], cwd=ROOT, check=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Explore Ilya reading-list research metadata for Signal Engine 2.0.")
    parser.add_argument("--list", action="store_true", help="List all papers.")
    parser.add_argument("--paper", help="Show one paper by id.")
    parser.add_argument("--category", choices=sorted(VALID_CATEGORIES), help="Show papers in a category.")
    parser.add_argument("--signal-engine-roadmap", action="store_true", help="Print roadmap-oriented paper mappings.")
    parser.add_argument("--export-markdown", action="store_true", help="Print a Markdown paper map.")
    parser.add_argument("--brief", help="Print the deep research brief for one paper id.")
    parser.add_argument("--parsed-status", action="store_true", help="Print source parse status for all papers.")
    parser.add_argument("--feature-backlog", action="store_true", help="Print the Signal Engine feature backlog.")
    parser.add_argument("--reading-plan", action="store_true", help="Print Keith's reading plan.")
    parser.add_argument("--source-registry", action="store_true", help="Print source registry summary.")
    parser.add_argument("--validate-full-asset", action="store_true", help="Run full research asset validation.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    selected = [
        args.list,
        bool(args.paper),
        bool(args.category),
        args.signal_engine_roadmap,
        args.export_markdown,
        bool(args.brief),
        args.parsed_status,
        args.feature_backlog,
        args.reading_plan,
        args.source_registry,
        args.validate_full_asset,
    ]
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
    elif args.brief:
        _print_brief(args.brief)
    elif args.parsed_status:
        _parsed_status()
    elif args.feature_backlog:
        _feature_backlog()
    elif args.reading_plan:
        _reading_plan()
    elif args.source_registry:
        _source_registry()
    elif args.validate_full_asset:
        _validate_full_asset()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
