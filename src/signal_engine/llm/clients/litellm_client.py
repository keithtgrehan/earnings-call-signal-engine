from __future__ import annotations

import json
import os
import time
from typing import Any

from ..config import LLMConfig
from ..providers import LIVE_ENV_FLAG, DryRunProvider
from ..safety import redact_secret_values
from ..types import LLMProviderResult, LLMRequest


class LiteLLMClient:
    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    def complete(self, request: LLMRequest, *, provider_name: str, live: bool = False) -> LLMProviderResult:
        if provider_name == "dry_run":
            return DryRunProvider().complete(request, live=False)
        provider_config = self.config.providers.get(provider_name)
        if provider_config is None:
            raise ValueError(f"unsupported LLM provider {provider_name}")
        model = os.getenv(provider_config.model_env, provider_config.default_model or f"{provider_name}-model")
        if not live:
            return LLMProviderResult(status="skipped", provider=provider_name, model=model, message="live flag was not requested")
        if os.getenv(LIVE_ENV_FLAG) != "1":
            return LLMProviderResult(status="skipped", provider=provider_name, model=model, message=f"{LIVE_ENV_FLAG}=1 is required for live provider calls")
        api_key = os.getenv(provider_config.api_key_env, "") if provider_config.api_key_env else ""
        if provider_config.api_key_env and not api_key:
            return LLMProviderResult(status="skipped", provider=provider_name, model=model, message=f"{provider_config.api_key_env} is not set")
        base_url = os.getenv(provider_config.base_url_env, "") if provider_config.base_url_env else ""
        if provider_name in {"glm52", "openai_compatible"} and provider_config.base_url_env and not base_url:
            return LLMProviderResult(status="skipped", provider=provider_name, model=model, message=f"{provider_config.base_url_env} is not set")
        try:
            import litellm  # type: ignore[import-not-found]
        except Exception:
            return LLMProviderResult(status="skipped", provider=provider_name, model=model, message="optional dependency litellm is not installed")

        started = time.monotonic()
        try:  # pragma: no cover - live provider path is opt-in and skipped in CI.
            response = litellm.completion(
                model=_litellm_model(provider_name, model),
                messages=[{"role": "user", "content": request.prompt}],
                api_key=api_key or None,
                api_base=base_url or None,
                temperature=0,
                max_tokens=1800,
            )
            text = _extract_litellm_text(response)
        except Exception as exc:  # pragma: no cover
            return LLMProviderResult(
                status="error",
                provider=provider_name,
                model=model,
                message=redact_secret_values(f"litellm provider call failed: {type(exc).__name__}: {exc}"),
            )
        return LLMProviderResult(
            status="ok",
            provider=provider_name,
            model=model,
            text=text,
            message="litellm provider call completed",
            latency_seconds=time.monotonic() - started,
        )


def _litellm_model(provider_name: str, model: str) -> str:
    if provider_name == "claude" and not model.startswith("anthropic/"):
        return f"anthropic/{model}"
    return model


def _extract_litellm_text(response: Any) -> str:
    choices = getattr(response, "choices", None)
    if choices:
        message = getattr(choices[0], "message", None)
        content = getattr(message, "content", None)
        if isinstance(content, str):
            return content
    if isinstance(response, dict):
        choices = response.get("choices", [])
        if choices and isinstance(choices[0], dict):
            message = choices[0].get("message", {})
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                return message["content"]
    return json.dumps(response, default=str)
