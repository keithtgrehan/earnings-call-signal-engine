from __future__ import annotations

from pathlib import Path
from typing import Any

from signal_engine.nlp_assets.registry import (
    VALID_CATEGORIES,
    VALID_DOWNLOAD_STATUSES,
    VALID_PRIORITIES,
    load_assets,
)


def filter_by_category(category: str, registry_path: str | Path | None = None) -> list[dict[str, Any]]:
    if category not in VALID_CATEGORIES:
        raise ValueError(f"Unknown NLP asset category: {category}")
    return [asset for asset in load_assets(registry_path) if asset.get("category") == category]


def filter_by_download_status(status: str, registry_path: str | Path | None = None) -> list[dict[str, Any]]:
    if status not in VALID_DOWNLOAD_STATUSES:
        raise ValueError(f"Unknown NLP asset download status: {status}")
    return [asset for asset in load_assets(registry_path) if asset.get("download_status") == status]


def filter_by_priority(priority: str, registry_path: str | Path | None = None) -> list[dict[str, Any]]:
    if priority not in VALID_PRIORITIES:
        raise ValueError(f"Unknown NLP asset priority: {priority}")
    return [asset for asset in load_assets(registry_path) if asset.get("priority") == priority]


def find_by_signal_engine_area(area: str, registry_path: str | Path | None = None) -> list[dict[str, Any]]:
    needle = area.lower()
    matches: list[dict[str, Any]] = []
    for asset in load_assets(registry_path):
        relevance = " ".join(asset.get("signal_engine_relevance", [])).lower()
        intended = " ".join(asset.get("intended_use", [])).lower()
        category = asset.get("category", "").lower()
        if needle in relevance or needle in intended or needle in category:
            matches.append(asset)
    return matches
