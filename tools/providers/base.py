from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
DESKTOP_WORKSPACE = Path("/Users/keith/Desktop/earnings calls 100 samples")
DEFAULT_REGISTRY = ROOT / "data" / "provider_registry.yaml"


@dataclass(frozen=True)
class ProviderConfig:
    provider_id: str
    name: str
    priority: int
    api_key_env: str
    enabled: bool
    metadata_discovery_allowed: bool
    raw_download_allowed: bool
    license_config_ref: str
    training_allowed: bool
    explicit_training_rights_ref: str

    @property
    def api_key_configured(self) -> bool:
        return bool(self.api_key_env and os.environ.get(self.api_key_env))

    @property
    def status(self) -> str:
        if not self.enabled:
            return "DISABLED"
        if self.api_key_env and not self.api_key_configured:
            return "NOT_CONFIGURED"
        if self.raw_download_allowed and not self.license_config_ref:
            return "LICENSE_CONFIG_REQUIRED"
        return "CONFIGURED_METADATA_ONLY" if not self.raw_download_allowed else "CONFIGURED_RAW_ALLOWED"


def load_provider_registry(path: Path = DEFAULT_REGISTRY) -> dict[str, ProviderConfig]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
    providers = payload.get("providers", {}) if isinstance(payload, dict) else {}
    configs: dict[str, ProviderConfig] = {}
    for provider_id, row in providers.items():
        configs[str(provider_id)] = ProviderConfig(
            provider_id=str(provider_id),
            name=str(row.get("name", provider_id)),
            priority=int(row.get("priority", 999)),
            api_key_env=str(row.get("api_key_env", "") or ""),
            enabled=bool(row.get("enabled", True)),
            metadata_discovery_allowed=bool(row.get("metadata_discovery_allowed", True)),
            raw_download_allowed=bool(row.get("raw_download_allowed", False)),
            license_config_ref=str(row.get("license_config_ref", "") or ""),
            training_allowed=bool(row.get("training_allowed", False)),
            explicit_training_rights_ref=str(row.get("explicit_training_rights_ref", "") or ""),
        )
    return dict(sorted(configs.items(), key=lambda item: item[1].priority))


def is_desktop_only_path(path: Path, workspace: Path = DESKTOP_WORKSPACE) -> bool:
    try:
        path.resolve().relative_to(workspace.resolve())
        return True
    except (OSError, ValueError):
        return False


def validate_raw_pull(config: ProviderConfig, output_path: Path, *, workspace: Path = DESKTOP_WORKSPACE) -> list[str]:
    errors: list[str] = []
    if config.api_key_env and not config.api_key_configured:
        errors.append("api_key_not_configured")
    if not config.license_config_ref:
        errors.append("license_config_ref_required")
    if not config.raw_download_allowed:
        errors.append("raw_download_allowed_false")
    if config.training_allowed and not config.explicit_training_rights_ref:
        errors.append("training_requires_explicit_training_rights_ref")
    if not is_desktop_only_path(output_path, workspace):
        errors.append("raw_target_must_be_desktop_workspace")
    return errors


class ProviderAdapter:
    provider_id = "base"

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    def discover_metadata(self, case: dict[str, str]) -> dict[str, Any]:
        if not self.config.metadata_discovery_allowed:
            return {"provider": self.provider_id, "case_id": case.get("case_id", ""), "status": "METADATA_DISCOVERY_DISABLED"}
        return {
            "provider": self.provider_id,
            "case_id": case.get("case_id", ""),
            "ticker": case.get("ticker", ""),
            "asset_type": "transcript_or_audio_metadata",
            "status": self.config.status,
            "raw_download_allowed": self.config.raw_download_allowed,
            "license_config_ref": self.config.license_config_ref,
            "training_allowed": self.config.training_allowed,
        }

    def download_raw(self, case: dict[str, str], output_path: Path) -> dict[str, Any]:
        errors = validate_raw_pull(self.config, output_path)
        if errors:
            return {
                "provider": self.provider_id,
                "case_id": case.get("case_id", ""),
                "status": "BLOCKED",
                "errors": errors,
                "raw_written": False,
            }
        return {
            "provider": self.provider_id,
            "case_id": case.get("case_id", ""),
            "status": "READY_FOR_PROVIDER_SPECIFIC_PULL",
            "errors": [],
            "raw_written": False,
        }
