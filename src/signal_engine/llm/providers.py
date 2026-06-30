from __future__ import annotations

import json
import os
import time
from typing import Any
from urllib import request as urllib_request

from .types import LLMProviderResult, LLMRequest

LIVE_ENV_FLAG = "SIGNAL_ENGINE_LLM_LIVE"


def _first_evidence(request: LLMRequest) -> dict[str, Any]:
    if request.evidence:
        return request.evidence[0]
    return {
        "source_id": "missing_evidence",
        "provenance_ref": "missing",
        "speaker_role": "unknown",
        "transcript_section": "unknown",
        "quote": "No transcript quote was provided.",
    }


def _json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)


class DryRunProvider:
    name = "dry_run"
    model = "dry-run-signal-engine-v1"

    def complete(self, request: LLMRequest, *, live: bool = False) -> LLMProviderResult:
        if request.task == "evidence_judge":
            text = _json_text(self._evidence_judge_payload(request))
        elif request.task == "reviewer_packet_assist":
            text = _json_text(self._reviewer_packet_payload(request))
        else:
            text = _json_text(self._signal_candidates_payload(request))
        return LLMProviderResult(status="ok", provider=self.name, model=self.model, text=text, message="dry-run provider used")

    def _signal_candidates_payload(self, request: LLMRequest) -> dict[str, Any]:
        evidence = _first_evidence(request)
        return {
            "schema_version": "llm_signal_candidates.v1",
            "request_id": request.request_id,
            "provider": self.name,
            "model": self.model,
            "output_role": "candidate",
            "canonical_output": False,
            "candidates": [
                {
                    "candidate_id": f"{request.request_id}-dry-run-1",
                    "signal_type": "guidance_revision",
                    "direction": "positive",
                    "confidence": "low",
                    "rationale": "Dry-run fixture candidate for offline validation only.",
                    "evidence": [
                        {
                            "source_id": str(evidence.get("source_id", "fixture")),
                            "provenance_ref": str(evidence.get("provenance_ref", "fixture")),
                            "speaker_role": str(evidence.get("speaker_role", "unknown")),
                            "transcript_section": str(evidence.get("transcript_section", "unknown")),
                            "quote": str(evidence.get("quote", "")),
                        }
                    ],
                }
            ],
        }

    def _evidence_judge_payload(self, request: LLMRequest) -> dict[str, Any]:
        evidence = _first_evidence(request)
        return {
            "schema_version": "llm_evidence_judge.v1",
            "request_id": request.request_id,
            "provider": self.name,
            "model": self.model,
            "output_role": "reviewer",
            "canonical_output": False,
            "judgments": [
                {
                    "candidate_id": f"{request.request_id}-dry-run-1",
                    "verdict": "supported",
                    "evidence_supported": True,
                    "evidence_quote": str(evidence.get("quote", "")),
                    "provenance_ref": str(evidence.get("provenance_ref", "fixture")),
                    "reason": "Dry-run judgment for offline validation only.",
                }
            ],
        }

    def _reviewer_packet_payload(self, request: LLMRequest) -> dict[str, Any]:
        evidence = _first_evidence(request)
        return {
            "schema_version": "llm_reviewer_packet_assist.v1",
            "request_id": request.request_id,
            "provider": self.name,
            "model": self.model,
            "output_role": "reviewer",
            "canonical_output": False,
            "reviewer_notes": [
                {
                    "note_type": "evidence_check",
                    "quote": str(evidence.get("quote", "")),
                    "provenance_ref": str(evidence.get("provenance_ref", "fixture")),
                    "note": "Dry-run reviewer assist output only.",
                }
            ],
        }


class _LiveProviderBase:
    name = "live"
    model_env_var = ""
    default_model = ""
    secret_env_var = ""

    def complete(self, request: LLMRequest, *, live: bool = False) -> LLMProviderResult:
        model = self._model()
        if not live:
            return self._skipped(model, "live flag was not requested")
        if os.getenv(LIVE_ENV_FLAG) != "1":
            return self._skipped(model, f"{LIVE_ENV_FLAG}=1 is required for live provider calls")
        api_key = os.getenv(self.secret_env_var, "")
        if not api_key:
            return self._skipped(model, f"{self.secret_env_var} is not set")
        started = time.monotonic()
        try:
            text = self._complete_live(request, api_key=api_key, model=model)
        except Exception as exc:  # pragma: no cover - live network path is opt-in and skipped in CI.
            return LLMProviderResult(status="error", provider=self.name, model=model, message=f"provider call failed: {type(exc).__name__}")
        return LLMProviderResult(
            status="ok",
            provider=self.name,
            model=model,
            text=text,
            message="provider call completed",
            latency_seconds=time.monotonic() - started,
        )

    def _model(self) -> str:
        return os.getenv(self.model_env_var, self.default_model)

    def _skipped(self, model: str, reason: str) -> LLMProviderResult:
        return LLMProviderResult(status="skipped", provider=self.name, model=model, message=reason)

    def _complete_live(self, request: LLMRequest, *, api_key: str, model: str) -> str:
        raise NotImplementedError


class ClaudeProvider(_LiveProviderBase):
    name = "claude"
    model_env_var = "ANTHROPIC_MODEL"
    default_model = "claude-sonnet-4-5"
    secret_env_var = "ANTHROPIC_API_KEY"

    def _complete_live(self, request: LLMRequest, *, api_key: str, model: str) -> str:
        body = {
            "model": model,
            "max_tokens": 1800,
            "messages": [{"role": "user", "content": request.prompt}],
        }
        req = urllib_request.Request(
            os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1/messages"),
            data=json.dumps(body).encode("utf-8"),
            headers={
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
                "x-api-key": api_key,
            },
            method="POST",
        )
        with urllib_request.urlopen(req, timeout=60) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
        content = payload.get("content", [])
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    return part["text"]
        return json.dumps(payload)


class GLM52Provider(_LiveProviderBase):
    name = "glm52"
    model_env_var = "GLM_MODEL"
    default_model = "glm-5.2"
    secret_env_var = "ZAI_API_KEY"

    def complete(self, request: LLMRequest, *, live: bool = False) -> LLMProviderResult:
        if live and os.getenv(LIVE_ENV_FLAG) == "1" and not os.getenv("ZAI_BASE_URL"):
            return self._skipped(self._model(), "ZAI_BASE_URL is not set")
        return super().complete(request, live=live)

    def _complete_live(self, request: LLMRequest, *, api_key: str, model: str) -> str:
        base_url = os.environ["ZAI_BASE_URL"].rstrip("/")
        body = {
            "model": model,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": 0,
            "max_tokens": 1800,
        }
        req = urllib_request.Request(
            f"{base_url}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "authorization": f"Bearer {api_key}",
                "content-type": "application/json",
            },
            method="POST",
        )
        with urllib_request.urlopen(req, timeout=60) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
        choices = payload.get("choices", [])
        if choices and isinstance(choices[0], dict):
            message = choices[0].get("message", {})
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                return message["content"]
        return json.dumps(payload)


def provider_for_name(name: str) -> DryRunProvider | ClaudeProvider | GLM52Provider:
    if name == "dry_run":
        return DryRunProvider()
    if name == "claude":
        return ClaudeProvider()
    if name == "glm52":
        return GLM52Provider()
    raise ValueError(f"unsupported LLM provider {name}")
