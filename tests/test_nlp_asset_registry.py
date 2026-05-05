from __future__ import annotations

import json
import subprocess
from pathlib import Path

from signal_engine.nlp_assets.registry import VALID_CATEGORIES, load_assets

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "nlp_assets" / "asset_registry.json"


def test_nlp_asset_registry_loads() -> None:
    assets = load_assets()
    assert len(assets) >= 60
    assert json.loads(REGISTRY_PATH.read_text(encoding="utf-8")) == assets


def test_required_fields_and_categories() -> None:
    required = {
        "id",
        "name",
        "category",
        "source_url",
        "license",
        "download_allowed",
        "download_status",
        "local_path",
        "committed",
        "intended_use",
        "signal_engine_relevance",
        "limitations",
        "priority",
    }
    valid_statuses = {"downloaded", "manual_required", "gated", "skipped", "unavailable"}
    for asset in load_assets():
        assert required <= set(asset)
        assert asset["category"] in VALID_CATEGORIES
        assert asset["download_status"] in valid_statuses
        assert asset["priority"] in {"high", "medium", "low"}
        assert asset["source_url"]
        assert asset["license"]
        assert asset["intended_use"]
        assert asset["signal_engine_relevance"]
        assert asset["limitations"]


def test_high_priority_assets_present() -> None:
    ids = {asset["id"] for asset in load_assets() if asset["priority"] == "high"}
    assert {
        "loughran_mcdonald_lexicon",
        "financial_phrasebank",
        "sec_company_tickers",
        "goemotions",
        "qasper",
        "rank_bm25",
        "presidio_analyzer",
        "faster_whisper",
    } <= ids


def test_no_large_raw_nlp_assets_committed() -> None:
    result = subprocess.run(["git", "ls-files"], cwd=ROOT, text=True, capture_output=True, check=True)
    blocked_suffixes = (".zip", ".tar", ".tar.gz", ".parquet", ".arrow")
    committed = [
        path
        for path in result.stdout.splitlines()
        if path.startswith("data/nlp_assets/") and path.lower().endswith(blocked_suffixes)
    ]
    assert committed == []
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "data/nlp_assets/cache/" in gitignore
    assert "data/nlp_assets/raw/" in gitignore
