#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "research" / "ilya_reading_list"
DOC_DIR = ROOT / "docs" / "research" / "ilya_reading_list"
VALID_PARSE_STATUSES = {"full_text_parsed", "abstract_only", "source_unavailable", "citation_only"}


def _tracked_files() -> list[str]:
    result = subprocess.run(["git", "ls-files"], cwd=ROOT, text=True, capture_output=True, check=True)
    return result.stdout.splitlines()


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the full Ilya paper research asset.")
    parser.add_argument("--registry", default=str(DATA_DIR / "source_registry.json"))
    args = parser.parse_args()

    registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    assert len(registry) == 26, "source registry must contain 26 papers"
    ids = {entry["id"] for entry in registry}
    assert len(ids) == 26, "paper ids must be unique"
    for entry in registry:
        assert entry.get("parse_status") in VALID_PARSE_STATUSES, entry["id"]
        assert entry.get("canonical_url") or entry.get("pdf_url") or entry.get("html_url"), entry["id"]
        assert entry.get("source_confidence") in {"high", "medium", "low"}, entry["id"]

    briefs = sorted((DOC_DIR / "papers").glob("*.md"))
    assert len(briefs) == 26, "expected one paper brief per paper"
    for brief in briefs:
        text = brief.read_text(encoding="utf-8")
        assert len(text) >= 2500, f"brief too short: {brief}"
        assert "## Signal Engine 2.0 Relevance" in text, brief
        assert "## Direct Feature Ideas" in text, brief

    backlog = DATA_DIR / "signal_engine_feature_backlog.csv"
    with backlog.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert rows, "feature backlog must have rows"

    assert (DOC_DIR / "keith_reading_plan.md").exists(), "Keith reading plan missing"
    tracked_pdfs = [
        path
        for path in _tracked_files()
        if path.startswith("data/research/ilya_reading_list/") and path.lower().endswith(".pdf")
    ]
    assert not tracked_pdfs, f"Research PDFs should not be committed: {tracked_pdfs}"
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "data/research/ilya_reading_list/cache/" in gitignore, "cache directory must be ignored"
    print("Research asset validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
