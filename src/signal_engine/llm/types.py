from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

LLMTask = Literal["signal_candidates", "evidence_judge", "reviewer_packet_assist"]
ProviderStatus = Literal["ok", "skipped", "error"]


@dataclass(frozen=True)
class LLMRequest:
    request_id: str
    task: LLMTask
    prompt: str
    evidence: list[dict[str, Any]]
    provider: str = "dry_run"
    model: str = "dry-run"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LLMProviderResult:
    status: ProviderStatus
    provider: str
    model: str
    text: str = ""
    message: str = ""
    latency_seconds: float | None = None
    estimated_cost_usd: float | None = None

    @property
    def provider_calls_performed(self) -> bool:
        return self.status == "ok" and self.provider != "dry_run"
