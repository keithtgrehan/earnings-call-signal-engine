from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from signal_engine.llm.types import LLMRequest

ROOT = Path(__file__).resolve().parents[1]


def _request() -> "LLMRequest":
    from signal_engine.llm.types import LLMRequest

    return LLMRequest(
        request_id="router-test-1",
        task="signal_candidates",
        prompt="Return strict JSON.",
        evidence=[
            {
                "source_id": "tiny_fixture",
                "provenance_ref": "tests/fixtures/tiny_realistic_earnings_excerpt.txt",
                "speaker_role": "management",
                "transcript_section": "prepared_remarks",
                "quote": "We are raising our revenue outlook for fiscal Q1 based on stronger enterprise demand.",
            }
        ],
    )


def test_litellm_router_constructs_without_live_dependency() -> None:
    from signal_engine.llm.router import LLMRouter
    from signal_engine.llm.validation import parse_and_validate_output

    router = LLMRouter(router="litellm", config_path=ROOT / "configs" / "llm.example.yml")
    result = router.complete(_request(), provider_name="dry_run", live=False)
    payload = parse_and_validate_output(result.text, output_type="signal_candidates")

    assert result.status == "ok"
    assert result.provider == "dry_run"
    assert payload["canonical_output"] is False


@pytest.mark.parametrize("provider_name", ["claude", "glm52", "openai_compatible"])
def test_router_refuses_live_providers_without_live_flag(provider_name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    from signal_engine.llm.router import LLMRouter

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-router-secret")
    monkeypatch.setenv("ZAI_API_KEY", "sk-zai-router-secret")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-router-secret")
    monkeypatch.setenv("ZAI_BASE_URL", "https://example.invalid")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.invalid")
    monkeypatch.delenv("SIGNAL_ENGINE_LLM_LIVE", raising=False)

    result = LLMRouter(config_path=ROOT / "configs" / "llm.example.yml").complete(
        _request(),
        provider_name=provider_name,
        live=True,
    )

    assert result.status == "skipped"
    assert "sk-ant-router-secret" not in result.message
    assert "sk-zai-router-secret" not in result.message
    assert "sk-openai-router-secret" not in result.message


def test_litellm_router_fails_closed_for_missing_optional_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    from signal_engine.llm.router import LLMRouter

    monkeypatch.setenv("SIGNAL_ENGINE_LLM_LIVE", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-router-secret")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.invalid")

    result = LLMRouter(router="litellm", config_path=ROOT / "configs" / "llm.example.yml").complete(
        _request(),
        provider_name="openai_compatible",
        live=True,
    )

    assert result.status in {"skipped", "error"}
    assert "sk-openai-router-secret" not in result.message
