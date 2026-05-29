from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from signal_engine.acquisition.asset_resolver import make_candidate


class ProviderStatus(str, Enum):
    CONFIGURED = "CONFIGURED"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    METADATA_ONLY = "METADATA_ONLY"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ProviderConfig:
    env: dict[str, str] = field(default_factory=dict)
    license_config_ref: str = ""
    provider_raw_use_allowed: bool = False


@dataclass(frozen=True)
class ProviderDiscoveryResult:
    provider_name: str
    status: ProviderStatus
    candidates: list[dict[str, str]]
    message: str = ""


class BaseProvider:
    name = "base"
    env_key = ""
    requires_license_for_raw = True

    def is_configured(self, config: ProviderConfig) -> bool:
        return not self.env_key or bool(config.env.get(self.env_key))

    def discover_assets(self, config: ProviderConfig, rows: list[dict[str, str]]) -> ProviderDiscoveryResult:
        if not self.is_configured(config):
            return ProviderDiscoveryResult(self.name, ProviderStatus.NOT_CONFIGURED, [], f"Missing {self.env_key}")
        if self.requires_license_for_raw and not (config.license_config_ref or config.provider_raw_use_allowed):
            candidates = [self._blocked_candidate(row, "vendor_raw_requires_license_config_ref") for row in self.provider_rows(rows)]
            return ProviderDiscoveryResult(self.name, ProviderStatus.BLOCKED, candidates, "license_config_ref required for raw vendor use")
        candidates = [self._candidate(row, config) for row in self.provider_rows(rows)]
        return ProviderDiscoveryResult(self.name, ProviderStatus.CONFIGURED, candidates, "configured")

    def provider_rows(self, rows: list[dict[str, str]]) -> list[dict[str, str]]:
        return rows

    def _candidate(self, row: dict[str, str], config: ProviderConfig) -> dict[str, str]:
        return make_candidate(
            row,
            asset_type=row.get("asset_type", "transcript_text"),
            source_type=self.name,
            source_url=row.get("source_url", row.get("resolved_asset_url", "")),
            resolved_asset_url=row.get("resolved_asset_url", row.get("source_url", "")),
            confidence=0.7,
            confidence_reason=f"{self.name} provider metadata",
            rights_status="licensed_provider_raw_allowed" if config.license_config_ref or config.provider_raw_use_allowed else "metadata_only",
            download_allowed=bool(config.license_config_ref or config.provider_raw_use_allowed),
            license_config_ref=config.license_config_ref,
            next_action="download" if config.license_config_ref or config.provider_raw_use_allowed else "metadata_review",
        )

    def _blocked_candidate(self, row: dict[str, str], blocked_reason: str) -> dict[str, str]:
        return make_candidate(
            row,
            asset_type="blocked",
            source_type=self.name,
            source_url=row.get("source_url", row.get("resolved_asset_url", "")),
            resolved_asset_url=row.get("resolved_asset_url", row.get("source_url", "")),
            confidence=0.0,
            confidence_reason=f"{self.name} provider blocked",
            rights_status="blocked",
            blocked_reason=blocked_reason,
            next_action="metadata_only_or_register_license",
        )


class StaticProvider(BaseProvider):
    def __init__(self, *, name: str, env_key: str, rows: list[dict[str, Any]], requires_license_for_raw: bool = True) -> None:
        self.name = name
        self.env_key = env_key
        self.rows = [{key: str(value) for key, value in row.items()} for row in rows]
        self.requires_license_for_raw = requires_license_for_raw

    def provider_rows(self, rows: list[dict[str, str]]) -> list[dict[str, str]]:
        return self.rows
