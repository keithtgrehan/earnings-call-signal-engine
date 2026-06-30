from __future__ import annotations

from pathlib import Path

from .clients.litellm_client import LiteLLMClient
from .config import LLMConfig, load_llm_config
from .providers import provider_for_name
from .types import LLMProviderResult, LLMRequest


class LLMRouter:
    def __init__(self, *, router: str = "direct", config_path: Path | str = "configs/llm.example.yml") -> None:
        if router not in {"direct", "litellm"}:
            raise ValueError("router must be direct or litellm")
        self.router = router
        self.config: LLMConfig = load_llm_config(config_path)

    def complete(self, request: LLMRequest, *, provider_name: str | None = None, live: bool = False) -> LLMProviderResult:
        selected_provider = provider_name or self.config.provider
        if self.router == "litellm":
            return LiteLLMClient(self.config).complete(request, provider_name=selected_provider, live=live)
        provider = provider_for_name(selected_provider)
        return provider.complete(request, live=live)
