from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_corpus_safe_check_invokes_only_safe_validators() -> None:
    result = subprocess.run(
        ["make", "-n", "corpus-safe-check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    output = result.stdout
    assert "validate_resource_registry.py" in output
    assert "check_restricted_artifacts.py --dry-run" in output
    assert "validate_retrieval_objects.py" in output
    assert "validate_retrieval_metrics.py" in output
    assert "validate_event_study_cases.py" in output
    assert "validate_training_plan.py" in output
    assert "validate_benchmark_registry.py" in output
    assert "validate_byok_reviewer_config.py" in output
    assert "validate_llm_config.py" in output
    assert "run_llm_fixture_smoke.py --provider dry_run" in output
    assert "check_llm_artifacts.py --root artifacts/llm --allow-missing" in output
    assert "intake_high_signal_transcripts.py" not in output
    assert "acquire_verified_transcripts.py" not in output


def test_llm_safe_check_uses_offline_dry_run_by_default() -> None:
    result = subprocess.run(
        ["make", "-n", "llm-safe-check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    output = result.stdout
    assert "validate_llm_config.py --path configs/llm.example.yml" in output
    assert "run_llm_fixture_smoke.py --provider dry_run" in output
    assert "check_llm_artifacts.py --root artifacts/llm --allow-missing" in output
    assert "ANTHROPIC_API_KEY" not in output
    assert "ZAI_API_KEY" not in output


def test_llm_router_and_optional_eval_targets_are_offline_by_default() -> None:
    result = subprocess.run(
        ["make", "-n", "llm-router-check", "llm-bakeoff", "promptfoo-check", "opik-check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    output = result.stdout
    assert "run_llm_fixture_smoke.py --provider dry_run --router litellm" in output
    assert "run_llm_bakeoff.py --providers dry_run --out reports/llm/llm_bakeoff.md" in output
    assert "promptfoo eval -c evals/promptfoo/llm_signal_extraction.yaml" in output
    assert "check_opik_config.py --path configs/opik.example.yml" in output
    assert "SIGNAL_ENGINE_LLM_LIVE=1" not in output
