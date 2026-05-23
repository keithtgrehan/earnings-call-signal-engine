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
    assert "intake_high_signal_transcripts.py" not in output
    assert "acquire_verified_transcripts.py" not in output


def test_real_pilot_targets_do_not_invoke_network_or_training() -> None:
    result = subprocess.run(
        ["make", "-n", "real-pilot-readiness-check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    output = result.stdout
    assert "build_nyse_5y_target_universe.py" in output
    assert "build_sec_metadata_queue.py" in output
    assert "build_agent1_retrieval_objects.py" in output
    assert "curl " not in output
    assert "wget " not in output
    assert "yt-dlp" not in output
    assert "train_" not in output
