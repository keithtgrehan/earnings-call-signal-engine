"""Config helpers for the optional NLP sidecar evaluation pack."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from earnings_call_sentiment.optional_runtime import load_multimodal_config

from .base import DEFAULT_BATCH_SIZE, DEFAULT_MAX_LENGTH

DEFAULT_MODELS = (
    "finbert_tone",
    "financial_roberta",
)
DEFAULT_ZERO_SHOT_LABEL_CONFIG = "finance"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_output_root() -> Path:
    return repo_root() / "outputs"


def default_zero_shot_config_path(name: str = DEFAULT_ZERO_SHOT_LABEL_CONFIG) -> Path:
    return repo_root() / "configs" / "nlp_sidecars" / f"zero_shot_labels.{name}.json"


def resolve_cache_dir() -> str | None:
    config = load_multimodal_config()
    for candidate in (config.model_cache_dir, config.transformers_cache, config.hf_home):
        if candidate is not None:
            return str(candidate)
    return None


def load_zero_shot_label_groups(path_or_name: str | Path | None = None) -> dict[str, list[str]]:
    if path_or_name is None:
        config_path = default_zero_shot_config_path()
    else:
        candidate = Path(str(path_or_name))
        config_path = candidate if candidate.suffix else default_zero_shot_config_path(str(path_or_name))
    resolved = config_path.expanduser().resolve()
    if not resolved.exists() or not resolved.is_file():
        raise RuntimeError(f"Zero-shot label config was not found: {resolved}")

    payload = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not payload:
        raise RuntimeError(f"Zero-shot label config must contain a non-empty mapping: {resolved}")

    groups: dict[str, list[str]] = {}
    for group_name, values in payload.items():
        if not isinstance(group_name, str) or not group_name.strip():
            raise RuntimeError(f"Zero-shot label config contains an invalid group name: {resolved}")
        if not isinstance(values, list) or not values:
            raise RuntimeError(
                f"Zero-shot label group '{group_name}' must contain a non-empty list."
            )
        labels = [str(value).strip() for value in values if str(value).strip()]
        if not labels:
            raise RuntimeError(
                f"Zero-shot label group '{group_name}' must contain non-empty labels."
            )
        groups[group_name.strip()] = labels
    return groups


def load_model_defaults() -> dict[str, Any]:
    config = load_multimodal_config()
    return {
        "device": config.multimodal_device,
        "batch_size": DEFAULT_BATCH_SIZE,
        "max_length": DEFAULT_MAX_LENGTH,
        "cache_dir": resolve_cache_dir(),
    }
