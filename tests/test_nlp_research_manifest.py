from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "build_nlp_research_manifest.py"


def test_nlp_research_manifest_builds_expected_outputs(tmp_path: Path) -> None:
    json_out = tmp_path / "research_manifest.json"
    markdown_out = tmp_path / "nlp_research_manifest.md"

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--json-out",
            str(json_out),
            "--markdown-out",
            str(markdown_out),
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(json_out.read_text(encoding="utf-8"))
    markdown = markdown_out.read_text(encoding="utf-8")

    assert payload["entry_count"] >= 18
    assert len(payload["entries"]) == payload["entry_count"]
    assert "NLP Research Manifest" in markdown
    assert "financial_nlp" in markdown
    assert "dialogue_acts" in markdown

    first = payload["entries"][0]
    assert {
        "title",
        "source_url",
        "type",
        "relevance_to_signal_engine",
        "license_or_access_notes",
        "downloaded_locally",
        "recommended_use",
    } <= set(first)


def test_nlp_research_manifest_includes_finance_and_conversation_sources(tmp_path: Path) -> None:
    json_out = tmp_path / "research_manifest.json"
    markdown_out = tmp_path / "nlp_research_manifest.md"

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--json-out",
            str(json_out),
            "--markdown-out",
            str(markdown_out),
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(json_out.read_text(encoding="utf-8"))
    titles = {entry["title"] for entry in payload["entries"]}

    assert "FinBERT: Financial Sentiment Analysis with Pre-trained Language Models" in titles
    assert "Financial PhraseBank" in titles
    assert "GoEmotions" in titles
    assert "BANKING77" in titles
