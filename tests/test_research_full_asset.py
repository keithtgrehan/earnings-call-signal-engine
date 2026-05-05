from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "research" / "ilya_reading_list"
DOC_DIR = ROOT / "docs" / "research" / "ilya_reading_list"


def test_all_papers_have_extracted_metadata_and_briefs() -> None:
    registry = json.loads((DATA_DIR / "source_registry.json").read_text(encoding="utf-8"))
    briefs = sorted((DOC_DIR / "papers").glob("*.md"))
    assert len(briefs) == 26
    for entry in registry:
        extracted = DATA_DIR / "extracted" / f"{entry['id']}.json"
        digest = DATA_DIR / "extracted" / f"{entry['id']}.txt"
        assert extracted.exists()
        assert digest.exists()
        payload = json.loads(extracted.read_text(encoding="utf-8"))
        assert payload["extraction_status"] == entry["parse_status"]
        assert payload["title"] == entry["title"]


def test_all_briefs_are_substantial_and_signal_engine_focused() -> None:
    for brief in (DOC_DIR / "papers").glob("*.md"):
        text = brief.read_text(encoding="utf-8")
        assert len(text) >= 2500
        assert "## Signal Engine 2.0 Relevance" in text
        assert "## Direct Feature Ideas" in text
        assert "## Implementation Backlog" in text
        assert "evidence span" in text.lower()


def test_feature_backlog_and_reading_plan_exist() -> None:
    with (DATA_DIR / "signal_engine_feature_backlog.csv").open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert len(rows) >= 26
    assert {"feature_id", "feature_name", "source_paper_ids", "evaluation_method"} <= set(rows[0])
    reading_plan = DOC_DIR / "keith_reading_plan.md"
    assert reading_plan.exists()
    assert "10-Paper Practical Fast Track" in reading_plan.read_text(encoding="utf-8")


def test_no_pdfs_are_tracked_and_cache_is_ignored() -> None:
    result = subprocess.run(["git", "ls-files"], cwd=ROOT, text=True, capture_output=True, check=True)
    tracked_pdfs = [
        path
        for path in result.stdout.splitlines()
        if path.startswith("data/research/ilya_reading_list/") and path.lower().endswith(".pdf")
    ]
    assert tracked_pdfs == []
    assert "data/research/ilya_reading_list/cache/" in (ROOT / ".gitignore").read_text(encoding="utf-8")


def test_validate_research_asset_script_passes() -> None:
    subprocess.run(
        [sys.executable, "tools/research_sources/validate_research_asset.py"],
        cwd=ROOT,
        check=True,
    )
