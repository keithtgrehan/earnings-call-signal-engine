from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ALLOWED_PROVIDER_SLOTS = (
    "openai_embedding",
    "voyage_embedding",
    "cohere_embedding",
    "jina_embedding",
    "cohere_rerank",
    "jina_rerank",
    "local_stub",
)
EMBEDDING_PROVIDER_SLOTS = {"openai_embedding", "voyage_embedding", "cohere_embedding", "jina_embedding"}
RERANKING_PROVIDER_SLOTS = {"cohere_rerank", "jina_rerank"}
REAL_PROVIDER_SLOTS = EMBEDDING_PROVIDER_SLOTS | RERANKING_PROVIDER_SLOTS

REQUIRED_PROVIDER_FIELDS = {"provider_type", "enabled", "mode", "network_enabled"}
REQUIRED_REAL_PROVIDER_FIELDS = REQUIRED_PROVIDER_FIELDS | {"model", "api_key_env"}
REQUIRED_OUTPUT_FIELDS = {"json_report", "markdown_report"}


@dataclass(frozen=True)
class ProviderSlotConfig:
    slot: str
    provider_type: str
    enabled: bool
    mode: str
    network_enabled: bool
    model: str = ""
    api_key_env: str = ""

    @property
    def is_real_provider(self) -> bool:
        return self.slot in REAL_PROVIDER_SLOTS


@dataclass(frozen=True)
class ProviderConfig:
    version: int
    status_label: str
    default_provider: str
    network_enabled: bool
    providers: dict[str, ProviderSlotConfig]
    outputs: dict[str, str]

    @property
    def default_slot(self) -> ProviderSlotConfig:
        return self.providers[self.default_provider]


def load_provider_config(path: Path) -> ProviderConfig:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("provider config must be a mapping")
    errors = validate_provider_config_payload(payload)
    if errors:
        raise ValueError("; ".join(errors))
    providers = {
        slot: ProviderSlotConfig(
            slot=slot,
            provider_type=str(raw["provider_type"]),
            enabled=bool(raw["enabled"]),
            mode=str(raw["mode"]),
            network_enabled=bool(raw["network_enabled"]),
            model=str(raw.get("model", "")),
            api_key_env=str(raw.get("api_key_env", "")),
        )
        for slot, raw in payload["providers"].items()
    }
    return ProviderConfig(
        version=int(payload["version"]),
        status_label=str(payload["status_label"]),
        default_provider=str(payload["default_provider"]),
        network_enabled=bool(payload["network_enabled"]),
        providers=providers,
        outputs={key: str(value) for key, value in payload["outputs"].items()},
    )


def validate_provider_config_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {"version", "status_label", "default_provider", "network_enabled", "providers", "outputs"}
    for field in sorted(required - set(payload)):
        errors.append(f"missing required config field {field}")
    for field in sorted(set(payload) - required):
        errors.append(f"unexpected config field {field}")
    if errors:
        return errors

    if payload.get("version") != 1:
        errors.append("version must be 1")
    if payload.get("status_label") != "retrieval_provider_adapter_scaffold_only":
        errors.append("status_label must be retrieval_provider_adapter_scaffold_only")
    if payload.get("default_provider") != "local_stub":
        errors.append("default_provider must be local_stub")
    if payload.get("network_enabled") is not False:
        errors.append("network_enabled must be false for scaffold dry runs")

    providers = payload.get("providers")
    if not isinstance(providers, dict):
        errors.append("providers must be a mapping")
        providers = {}
    outputs = payload.get("outputs")
    if not isinstance(outputs, dict):
        errors.append("outputs must be a mapping")
        outputs = {}

    for slot in sorted(set(providers) - set(ALLOWED_PROVIDER_SLOTS)):
        errors.append(f"unknown provider slot {slot}")
    for slot in ALLOWED_PROVIDER_SLOTS:
        if slot not in providers:
            errors.append(f"missing provider slot {slot}")
            continue
        raw = providers[slot]
        if not isinstance(raw, dict):
            errors.append(f"provider {slot} must be a mapping")
            continue
        required_fields = REQUIRED_REAL_PROVIDER_FIELDS if slot in REAL_PROVIDER_SLOTS else REQUIRED_PROVIDER_FIELDS | {"model"}
        for field in sorted(required_fields - set(raw)):
            errors.append(f"provider {slot} missing required field {field}")
        for field in sorted(set(raw) - required_fields):
            errors.append(f"provider {slot} unexpected field {field}")
        if raw.get("provider_type") != slot:
            errors.append(f"provider {slot} provider_type must equal slot name")
        if not isinstance(raw.get("enabled"), bool):
            errors.append(f"provider {slot} enabled must be boolean")
        if not isinstance(raw.get("network_enabled"), bool):
            errors.append(f"provider {slot} network_enabled must be boolean")
        if slot == "local_stub":
            if raw.get("enabled") is not True:
                errors.append("provider local_stub enabled must be true")
            if raw.get("mode") != "dry_run":
                errors.append("provider local_stub mode must be dry_run")
            if raw.get("network_enabled") is not False:
                errors.append("provider local_stub network_enabled must be false")
        else:
            if raw.get("enabled") is not False:
                errors.append(f"provider {slot} must remain disabled in scaffold config")
            if raw.get("mode") != "disabled":
                errors.append(f"provider {slot} mode must be disabled")
            if raw.get("network_enabled") is not False:
                errors.append(f"provider {slot} network_enabled must be false")
            if not str(raw.get("model", "")).strip():
                errors.append(f"provider {slot} model must be present")
            if not str(raw.get("api_key_env", "")).strip():
                errors.append(f"provider {slot} api_key_env must be present")

    for field in sorted(REQUIRED_OUTPUT_FIELDS - set(outputs)):
        errors.append(f"outputs missing required field {field}")
    for field in sorted(set(outputs) - REQUIRED_OUTPUT_FIELDS):
        errors.append(f"outputs unexpected field {field}")
    for field, value in outputs.items():
        if not isinstance(value, str) or not value.strip():
            errors.append(f"outputs {field} must be a non-empty string")
    return errors
