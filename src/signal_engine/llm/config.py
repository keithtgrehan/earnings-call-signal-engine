from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ALLOWED_USE_CASES = {"reviewer_support", "extraction_benchmark"}
ALLOWED_OUTPUT_ROOTS = {"artifacts/llm", "reports/llm"}
SUPPORTED_PROVIDERS = {"dry_run", "claude", "glm52", "openai_compatible"}


@dataclass(frozen=True)
class LLMProviderConfig:
    name: str
    provider_type: str
    enabled: bool
    default_model: str = ""
    model_env: str = ""
    api_key_env: str = ""
    base_url_env: str = ""
    notes: str = ""

    @property
    def model_env_var_name(self) -> str:
        return self.model_env

    @property
    def secret_env_var_name(self) -> str:
        return self.api_key_env

    @property
    def base_url_env_var_name(self) -> str:
        return self.base_url_env


@dataclass(frozen=True)
class LLMConfig:
    schema_version: str
    enabled: bool
    provider: str
    mode: str
    allow_network: bool
    require_live_flag: bool
    require_quote_evidence: bool
    require_json_schema: bool
    canonical_output: bool
    auto_promote_gold: bool
    output_dir: str
    report_dir: str
    max_calls: int
    max_cost_usd: float
    allowed_use_cases: tuple[str, ...]
    providers: dict[str, LLMProviderConfig]

    @property
    def allow_live_provider_calls(self) -> bool:
        return self.allow_network

    @property
    def canonical_output_allowed(self) -> bool:
        return self.canonical_output

    @property
    def default_provider(self) -> str:
        return self.provider

    @property
    def allowed_output_roots(self) -> tuple[str, ...]:
        return (self.output_dir.rstrip("/"), self.report_dir.rstrip("/"))


def _looks_like_secret(value: Any) -> bool:
    text = str(value or "").strip()
    lowered = text.lower()
    return lowered.startswith(("sk-", "pk-", "ak-")) or "secret" in lowered or "api_key=" in lowered


def _is_env_var_name(value: str) -> bool:
    if not value:
        return True
    return value.replace("_", "").isalnum() and value.upper() == value and not value[0].isdigit()


def _llm_section(payload: dict[str, Any]) -> dict[str, Any]:
    llm_payload = payload.get("llm")
    if isinstance(llm_payload, dict):
        return llm_payload
    return payload


def validate_llm_config_payload(payload: dict[str, Any], *, require_disabled_default: bool = False) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != "llm_backends.v1":
        errors.append("schema_version must be llm_backends.v1")
    llm_payload = _llm_section(payload)
    required_llm = {
        "enabled",
        "provider",
        "mode",
        "allow_network",
        "require_live_flag",
        "require_quote_evidence",
        "require_json_schema",
        "canonical_output",
        "auto_promote_gold",
        "output_dir",
        "report_dir",
        "max_calls",
        "max_cost_usd",
        "allowed_use_cases",
    }
    for field in sorted(required_llm - set(llm_payload)):
        errors.append(f"missing required llm field {field}")

    if require_disabled_default and llm_payload.get("enabled") is not False:
        errors.append("enabled must be false in the default example config")
    if llm_payload.get("canonical_output") is not False:
        errors.append("canonical_output must be false")
    if llm_payload.get("auto_promote_gold") is not False:
        errors.append("auto_promote_gold must be false")
    if require_disabled_default and llm_payload.get("allow_network") is not False:
        errors.append("allow_network must be false in the default example config")
    if llm_payload.get("require_live_flag") is not True:
        errors.append("require_live_flag must be true")
    if llm_payload.get("require_quote_evidence") is not True:
        errors.append("require_quote_evidence must be true")
    if llm_payload.get("require_json_schema") is not True:
        errors.append("require_json_schema must be true")

    use_cases = llm_payload.get("allowed_use_cases")
    if not isinstance(use_cases, list) or not use_cases:
        errors.append("allowed_use_cases must be a non-empty list")
    else:
        invalid = sorted({str(item) for item in use_cases} - ALLOWED_USE_CASES)
        if invalid:
            errors.append(f"unsupported allowed_use_cases: {', '.join(invalid)}")

    roots = {str(llm_payload.get("output_dir", "")).rstrip("/"), str(llm_payload.get("report_dir", "")).rstrip("/")}
    invalid_roots = sorted(roots - ALLOWED_OUTPUT_ROOTS)
    if invalid_roots:
        errors.append(f"LLM outputs may only write under artifacts/llm or reports/llm: {', '.join(invalid_roots)}")
    if not isinstance(llm_payload.get("max_calls"), int) or isinstance(llm_payload.get("max_calls"), bool) or llm_payload.get("max_calls", 0) < 0:
        errors.append("max_calls must be a non-negative integer")
    try:
        if float(llm_payload.get("max_cost_usd", -1)) < 0:
            errors.append("max_cost_usd must be non-negative")
    except (TypeError, ValueError):
        errors.append("max_cost_usd must be numeric")

    default_provider = str(llm_payload.get("provider", ""))
    if default_provider not in SUPPORTED_PROVIDERS:
        errors.append("provider must be one of dry_run, claude, glm52, openai_compatible")
    if require_disabled_default and default_provider != "dry_run":
        errors.append("provider must default to dry_run")
    if require_disabled_default and llm_payload.get("mode") != "dry_run":
        errors.append("mode must default to dry_run")

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
        for env_field in ("api_key_env", "base_url_env", "model_env", "secret_env_var_name", "base_url_env_var_name", "model_env_var_name"):
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
        default_model=str(payload.get("default_model", "") or ""),
        model_env=str(payload.get("model_env", payload.get("model_env_var_name", "")) or ""),
        api_key_env=str(payload.get("api_key_env", payload.get("secret_env_var_name", "")) or ""),
        base_url_env=str(payload.get("base_url_env", payload.get("base_url_env_var_name", "")) or ""),
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
    llm_payload = _llm_section(payload)
    providers = {
        name: _provider_config(name, provider_payload)
        for name, provider_payload in payload["providers"].items()
        if isinstance(provider_payload, dict)
    }
    return LLMConfig(
        schema_version=str(payload["schema_version"]),
        enabled=bool(llm_payload["enabled"]),
        provider=str(llm_payload["provider"]),
        mode=str(llm_payload["mode"]),
        allow_network=bool(llm_payload["allow_network"]),
        require_live_flag=bool(llm_payload["require_live_flag"]),
        require_quote_evidence=bool(llm_payload["require_quote_evidence"]),
        require_json_schema=bool(llm_payload["require_json_schema"]),
        canonical_output=bool(llm_payload["canonical_output"]),
        auto_promote_gold=bool(llm_payload["auto_promote_gold"]),
        output_dir=str(llm_payload["output_dir"]).rstrip("/"),
        report_dir=str(llm_payload["report_dir"]).rstrip("/"),
        max_calls=int(llm_payload["max_calls"]),
        max_cost_usd=float(llm_payload["max_cost_usd"]),
        allowed_use_cases=tuple(str(item) for item in llm_payload["allowed_use_cases"]),
        providers=providers,
    )
