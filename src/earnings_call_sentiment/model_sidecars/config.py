"""Config loading for model-sidecar evaluation presets."""

from __future__ import annotations

from pathlib import Path

from earnings_call_sentiment import optional_runtime


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_zero_shot_config_path() -> Path:
    return repo_root() / "configs" / "model_eval" / "zero_shot_labels.default.yaml"


def load_zero_shot_label_groups(path: str | Path | None = None) -> dict[str, list[str]]:
    yaml = optional_runtime.load_optional_dependency("yaml", package_name="PyYAML")
    config_path = Path(path) if path is not None else default_zero_shot_config_path()
    resolved = config_path.expanduser().resolve()
    if not resolved.exists() or not resolved.is_file():
        raise RuntimeError(f"Zero-shot label config was not found: {resolved}")

    payload = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not payload:
        raise RuntimeError(
            f"Zero-shot label config must contain a non-empty mapping: {resolved}"
        )

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
