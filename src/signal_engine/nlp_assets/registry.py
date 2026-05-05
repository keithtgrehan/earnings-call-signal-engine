from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REGISTRY_PATH = REPO_ROOT / "data" / "nlp_assets" / "asset_registry.json"

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

VALID_DOWNLOAD_STATUSES = {"downloaded", "manual_required", "gated", "skipped", "unavailable"}
VALID_PRIORITIES = {"high", "medium", "low"}


def load_assets(registry_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Load the committed NLP asset registry."""
    path = Path(registry_path) if registry_path is not None else DEFAULT_REGISTRY_PATH
    with path.open(encoding="utf-8") as file:
        assets = json.load(file)
    if not isinstance(assets, list):
        raise ValueError(f"Expected a list of NLP assets in {path}")
    return assets
