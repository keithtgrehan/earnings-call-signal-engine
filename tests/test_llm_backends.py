from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import TYPE_CHECKING
from pathlib import Path

import pytest

if TYPE_CHECKING:
    from signal_engine.llm.types import LLMRequest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "tiny_realistic_earnings_excerpt.txt"


def _request() -> "LLMRequest":
    from signal_engine.llm.types import LLMRequest

    return LLMRequest(
        request_id="test-request-1",
        task="signal_candidates",
        prompt="Return candidate signals as strict JSON.",
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


def test_default_llm_config_is_disabled() -> None:
    from signal_engine.llm.config import load_llm_config

    config = load_llm_config(ROOT / "configs" / "llm.example.yml")

    assert config.enabled is False
    assert config.provider == "dry_run"
    assert config.mode == "dry_run"
    assert config.allow_network is False
    assert config.allow_live_provider_calls is False
    assert config.canonical_output_allowed is False
    assert config.auto_promote_gold is False
    assert config.output_dir == "artifacts/llm"
    assert config.report_dir == "reports/llm"
    assert config.max_calls == 10
    assert config.max_cost_usd == 5.00
    assert set(config.allowed_use_cases) == {"reviewer_support", "extraction_benchmark"}
    assert set(config.allowed_output_roots) == {"artifacts/llm", "reports/llm"}
    assert "openai_compatible" in config.providers


def test_dry_run_provider_returns_valid_signal_candidates_offline() -> None:
    from signal_engine.llm.providers import DryRunProvider
    from signal_engine.llm.validation import parse_and_validate_output

    result = DryRunProvider().complete(_request(), live=False)
    payload = parse_and_validate_output(result.text, output_type="signal_candidates")

    assert result.status == "ok"
    assert payload["canonical_output"] is False
    assert payload["output_role"] == "candidate"
    assert payload["candidates"][0]["evidence"][0]["quote"] == _request().evidence[0]["quote"]


def test_invalid_json_fails_closed() -> None:
    from signal_engine.llm.validation import LLMOutputValidationError, parse_and_validate_output

    with pytest.raises(LLMOutputValidationError, match="valid JSON"):
        parse_and_validate_output("not json", output_type="signal_candidates")


def test_missing_evidence_quote_fails_validation() -> None:
    from signal_engine.llm.validation import LLMOutputValidationError, validate_output_payload

    payload = {
        "schema_version": "llm_signal_candidates.v1",
        "request_id": "test-request-1",
        "provider": "dry_run",
        "model": "dry-run",
        "output_role": "candidate",
        "canonical_output": False,
        "candidates": [
            {
                "candidate_id": "cand-1",
                "signal_type": "guidance_revision",
                "direction": "positive",
                "confidence": "low",
                "rationale": "A test candidate.",
                "evidence": [
                    {
                        "source_id": "tiny_fixture",
                        "provenance_ref": "tests/fixtures/tiny_realistic_earnings_excerpt.txt",
                        "speaker_role": "management",
                        "transcript_section": "prepared_remarks",
                    }
                ],
            }
        ],
    }

    with pytest.raises(LLMOutputValidationError, match="quote"):
        validate_output_payload(payload, output_type="signal_candidates")


def test_live_providers_skip_without_explicit_runtime_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    from signal_engine.llm.providers import ClaudeProvider, GLM52Provider, OpenAICompatibleProvider

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-secret")
    monkeypatch.setenv("ZAI_API_KEY", "sk-zai-test-secret")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-test-secret")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.invalid")
    monkeypatch.delenv("SIGNAL_ENGINE_LLM_LIVE", raising=False)

    for provider in (ClaudeProvider(), GLM52Provider(), OpenAICompatibleProvider()):
        result = provider.complete(_request(), live=True)
        assert result.status == "skipped"
        assert "sk-ant-test-secret" not in result.message
        assert "sk-zai-test-secret" not in result.message
        assert "sk-openai-test-secret" not in result.message


def test_llm_smoke_script_does_not_print_api_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "sk-ant-secret-should-not-appear"
    out_path = ROOT / "artifacts" / "llm" / "test_key_redaction_smoke.json"
    if out_path.exists():
        out_path.unlink()

    env = os.environ.copy()
    env["ANTHROPIC_API_KEY"] = secret
    env.pop("SIGNAL_ENGINE_LLM_LIVE", None)

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_llm_fixture_smoke.py"),
            "--provider",
            "claude",
            "--fixture",
            str(FIXTURE),
            "--out",
            str(out_path),
        ],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    try:
        combined_logs = result.stdout + result.stderr
        assert result.returncode == 0, combined_logs
        assert secret not in combined_logs
        assert out_path.exists()
        assert secret not in out_path.read_text(encoding="utf-8")
        payload = json.loads(out_path.read_text(encoding="utf-8"))
        assert payload["status"] == "skipped"
    finally:
        if out_path.exists():
            out_path.unlink()
