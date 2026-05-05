from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from signal_engine.research.paper_metadata import VALID_CATEGORIES, filter_by_category, get_paper, load_papers

ROOT = Path(__file__).resolve().parents[1]
METADATA_PATH = ROOT / "data" / "research" / "ilya_reading_list" / "papers_metadata.json"
CLI_PATH = ROOT / "tools" / "research_paper_map.py"


def test_research_metadata_json_loads() -> None:
    payload = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert len(payload) == 26


def test_required_paper_fields_and_categories() -> None:
    required = {
        "id",
        "title",
        "authors",
        "year",
        "category",
        "core_concepts",
        "signal_engine_relevance",
        "future_features",
        "implementation_status",
        "confidence",
        "source_urls",
    }
    for paper in load_papers():
        assert required <= set(paper)
        assert paper["category"] in VALID_CATEGORIES
        assert paper["implementation_status"] in {"research_only", "scaffolded", "implemented"}
        assert paper["confidence"] in {"high", "medium", "low"}
        assert paper["source_urls"]


def test_metadata_helpers_find_attention_category() -> None:
    paper = get_paper("attention_is_all_you_need")
    assert paper["title"] == "Attention Is All You Need"
    attention_papers = filter_by_category("attention_transformers")
    assert any(item["id"] == "pointer_networks" for item in attention_papers)


def test_cli_actions_do_not_crash() -> None:
    commands = [
        ["--list"],
        ["--paper", "attention_is_all_you_need"],
        ["--category", "attention_transformers"],
        ["--signal-engine-roadmap"],
        ["--export-markdown"],
    ]
    for command in commands:
        result = subprocess.run(
            [sys.executable, str(CLI_PATH), *command],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        assert result.stdout.strip()
