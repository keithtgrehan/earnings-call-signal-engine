"""Config loading for model-sidecar evaluation presets and batch manifests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from earnings_call_sentiment import optional_runtime


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_zero_shot_config_path() -> Path:
    return repo_root() / "configs" / "model_eval" / "zero_shot_labels.default.yaml"


def default_manifest_dir() -> Path:
    return repo_root() / "configs" / "model_eval" / "manifests"


def _load_yaml_mapping(path: str | Path) -> tuple[Path, dict[str, Any]]:
    yaml = optional_runtime.load_optional_dependency("yaml", package_name="PyYAML")
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists() or not resolved.is_file():
        raise RuntimeError(f"YAML config was not found: {resolved}")

    payload = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not payload:
        raise RuntimeError(f"YAML config must contain a non-empty mapping: {resolved}")
    return resolved, payload


def load_zero_shot_label_groups(path: str | Path | None = None) -> dict[str, list[str]]:
    config_path = Path(path) if path is not None else default_zero_shot_config_path()
    resolved, payload = _load_yaml_mapping(config_path)

    groups: dict[str, list[str]] = {}
    for group_name, values in payload.items():
        if not isinstance(group_name, str) or not group_name.strip():
            raise RuntimeError(
                f"Zero-shot label config contains an invalid group name: {resolved}"
            )
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


def load_sidecar_manifest(path: str | Path) -> dict[str, Any]:
    resolved, payload = _load_yaml_mapping(path)

    normalized: dict[str, Any] = {
        "manifest_path": str(resolved),
        "name": str(payload.get("name") or resolved.stem),
    }

    for key in ("case_ids", "models", "units"):
        values = payload.get(key)
        if not isinstance(values, list) or not values:
            raise RuntimeError(f"Manifest field '{key}' must contain a non-empty list.")
        items = [str(value).strip() for value in values if str(value).strip()]
        if not items:
            raise RuntimeError(f"Manifest field '{key}' must contain non-empty values.")
        normalized[key] = items

    if payload.get("zero_shot_label_config"):
        normalized["zero_shot_label_config"] = str(payload["zero_shot_label_config"]).strip()
    if payload.get("device_expectation"):
        normalized["device_expectation"] = str(payload["device_expectation"]).strip()
    if payload.get("output_root"):
        normalized["output_root"] = str(payload["output_root"]).strip()
    if payload.get("notes"):
        notes = payload["notes"]
        if isinstance(notes, list):
            normalized["notes"] = [str(item).strip() for item in notes if str(item).strip()]
        else:
            normalized["notes"] = [str(notes).strip()]

    for key in ("batch_size", "max_length", "sample_size", "limit", "seed"):
        value = payload.get(key)
        if value is None:
            continue
        try:
            normalized[key] = int(value)
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"Manifest field '{key}' must be an integer.") from exc

    if payload.get("sample_strategy"):
        normalized["sample_strategy"] = str(payload["sample_strategy"]).strip().lower()
    if payload.get("run_mode"):
        normalized["run_mode"] = str(payload["run_mode"]).strip().lower()

    return normalized
