from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ALLOWED_USE_CASES = {"reviewer_support", "extraction_benchmark"}
ALLOWED_OUTPUT_ROOTS = {"artifacts/llm", "reports/llm"}
SUPPORTED_PROVIDERS = {"dry_run", "claude", "glm52"}


@dataclass(frozen=True)
class LLMProviderConfig:
    name: str
    provider_type: str
    enabled: bool
    model_env_var_name: str = ""
    default_model: str = ""
    secret_env_var_name: str = ""
    base_url_env_var_name: str = ""
    notes: str = ""


@dataclass(frozen=True)
class LLMConfig:
    schema_version: str
    enabled: bool
    allow_live_provider_calls: bool
    canonical_output_allowed: bool
    auto_promote_gold: bool
    allowed_use_cases: tuple[str, ...]
    allowed_output_roots: tuple[str, ...]
    default_provider: str
    providers: dict[str, LLMProviderConfig]


def _looks_like_secret(value: Any) -> bool:
    text = str(value or "").strip()
    lowered = text.lower()
    return lowered.startswith(("sk-", "pk-", "ak-")) or "secret" in lowered or "api_key=" in lowered


def _is_env_var_name(value: str) -> bool:
    if not value:
        return True
    return value.replace("_", "").isalnum() and value.upper() == value and not value[0].isdigit()


def validate_llm_config_payload(payload: dict[str, Any], *, require_disabled_default: bool = False) -> list[str]:
    errors: list[str] = []
    required = {
        "schema_version",
        "enabled",
        "allow_live_provider_calls",
        "canonical_output_allowed",
        "auto_promote_gold",
        "allowed_use_cases",
        "allowed_output_roots",
        "default_provider",
        "providers",
    }
    for field in sorted(required - set(payload)):
        errors.append(f"missing required field {field}")

    if require_disabled_default and payload.get("enabled") is not False:
        errors.append("enabled must be false in the default example config")
    if payload.get("canonical_output_allowed") is not False:
        errors.append("canonical_output_allowed must be false")
    if payload.get("auto_promote_gold") is not False:
        errors.append("auto_promote_gold must be false")
    if require_disabled_default and payload.get("allow_live_provider_calls") is not False:
        errors.append("allow_live_provider_calls must be false in the default example config")

    use_cases = payload.get("allowed_use_cases")
    if not isinstance(use_cases, list) or not use_cases:
        errors.append("allowed_use_cases must be a non-empty list")
    else:
        invalid = sorted({str(item) for item in use_cases} - ALLOWED_USE_CASES)
        if invalid:
            errors.append(f"unsupported allowed_use_cases: {', '.join(invalid)}")

    roots = payload.get("allowed_output_roots")
    if not isinstance(roots, list) or not roots:
        errors.append("allowed_output_roots must be a non-empty list")
    else:
        invalid_roots = sorted({str(item).rstrip('/') for item in roots} - ALLOWED_OUTPUT_ROOTS)
        if invalid_roots:
            errors.append(f"LLM outputs may only write under artifacts/llm or reports/llm: {', '.join(invalid_roots)}")

    default_provider = str(payload.get("default_provider", ""))
    if default_provider not in SUPPORTED_PROVIDERS:
        errors.append("default_provider must be one of dry_run, claude, glm52")

    providers = payload.get("providers")
    if not isinstance(providers, dict):
        errors.append("providers must be an object")
        return errors
    for provider_name in sorted(SUPPORTED_PROVIDERS - set(providers)):
        errors.append(f"missing provider config {provider_name}")
    for provider_name, provider_payload in providers.items():
        if provider_name not in SUPPORTED_PROVIDERS:
            errors.append(f"unsupported provider {provider_name}")
        if not isinstance(provider_payload, dict):
            errors.append(f"provider {provider_name} must be an object")
            continue
        for env_field in ("secret_env_var_name", "base_url_env_var_name", "model_env_var_name"):
            value = str(provider_payload.get(env_field, "") or "")
            if _looks_like_secret(value):
                errors.append(f"provider {provider_name}: {env_field} must name an environment variable, not contain a secret")
            if not _is_env_var_name(value):
                errors.append(f"provider {provider_name}: {env_field} must be an uppercase environment variable name")
        if provider_name != "dry_run" and provider_payload.get("enabled") is not False and require_disabled_default:
            errors.append(f"provider {provider_name} must be disabled in the default example config")
    return errors


def _provider_config(name: str, payload: dict[str, Any]) -> LLMProviderConfig:
    return LLMProviderConfig(
        name=name,
        provider_type=str(payload.get("provider_type", name)),
        enabled=bool(payload.get("enabled", False)),
        model_env_var_name=str(payload.get("model_env_var_name", "") or ""),
        default_model=str(payload.get("default_model", "") or ""),
        secret_env_var_name=str(payload.get("secret_env_var_name", "") or ""),
        base_url_env_var_name=str(payload.get("base_url_env_var_name", "") or ""),
        notes=str(payload.get("notes", "") or ""),
    )


def load_llm_config(path: Path | str = "configs/llm.example.yml") -> LLMConfig:
    resolved = Path(path)
    payload = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("LLM config must be a YAML object.")
    errors = validate_llm_config_payload(payload)
    if errors:
        raise ValueError("; ".join(errors))
    providers = {
        name: _provider_config(name, provider_payload)
        for name, provider_payload in payload["providers"].items()
        if isinstance(provider_payload, dict)
    }
    return LLMConfig(
        schema_version=str(payload["schema_version"]),
        enabled=bool(payload["enabled"]),
        allow_live_provider_calls=bool(payload["allow_live_provider_calls"]),
        canonical_output_allowed=bool(payload["canonical_output_allowed"]),
        auto_promote_gold=bool(payload["auto_promote_gold"]),
        allowed_use_cases=tuple(str(item) for item in payload["allowed_use_cases"]),
        allowed_output_roots=tuple(str(item).rstrip("/") for item in payload["allowed_output_roots"]),
        default_provider=str(payload["default_provider"]),
        providers=providers,
    )
