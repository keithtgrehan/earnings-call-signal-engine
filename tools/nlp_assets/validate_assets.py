#!/usr/bin/env python
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_JSON = ROOT / "data" / "nlp_assets" / "asset_registry.json"
VALID_CATEGORIES = {
    "finance",
    "sentiment_emotion",
    "intent",
    "qa_retrieval",
    "dialogue",
    "weak_labeling",
    "evaluation_safety",
    "embeddings_retrieval_tools",
    "local_nlp_tools",
    "privacy",
    "audio_asr_prosody",
    "video_multimodal",
}
VALID_STATUSES = {"downloaded", "manual_required", "gated", "skipped", "unavailable"}
VALID_PRIORITIES = {"high", "medium", "low"}
REQUIRED_FIELDS = {
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


def _tracked_files() -> list[str]:
    result = subprocess.run(["git", "ls-files"], cwd=ROOT, text=True, capture_output=True, check=True)
    return result.stdout.splitlines()


def main() -> int:
    entries = json.loads(REGISTRY_JSON.read_text(encoding="utf-8"))
    assert len(entries) >= 60, "expected broad NLP asset registry"
    ids = {entry["id"] for entry in entries}
    assert len(ids) == len(entries), "asset ids must be unique"
    for entry in entries:
        assert REQUIRED_FIELDS <= set(entry), entry.get("id")
        assert entry["category"] in VALID_CATEGORIES, entry["id"]
        assert entry["download_status"] in VALID_STATUSES, entry["id"]
        assert entry["priority"] in VALID_PRIORITIES, entry["id"]
        assert entry["source_url"], entry["id"]
        assert entry["license"], entry["id"]
        assert entry["intended_use"], entry["id"]
        assert entry["signal_engine_relevance"], entry["id"]
        assert entry["limitations"], entry["id"]
    for required_id in ["loughran_mcdonald_lexicon", "financial_phrasebank", "sec_company_tickers", "goemotions", "rank_bm25", "faster_whisper", "cmu_mosei"]:
        assert required_id in ids, required_id
    tracked_bad = [
        path
        for path in _tracked_files()
        if path.startswith("data/nlp_assets/")
        and path.lower().endswith((".zip", ".tar", ".tar.gz", ".parquet", ".arrow"))
    ]
    assert tracked_bad == [], f"large/raw NLP assets should not be committed: {tracked_bad}"
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "data/nlp_assets/cache/" in gitignore
    assert "data/nlp_assets/raw/" in gitignore
    print("NLP asset registry validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
