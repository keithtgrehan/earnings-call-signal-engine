from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
READINESS_SCRIPT = ROOT / "scripts" / "run_training_readiness.py"
SMOKE_SCRIPT = ROOT / "scripts" / "run_signal_baseline_smoke_train.py"


def test_training_readiness_default_is_not_ready() -> None:
    result = subprocess.run(
        [sys.executable, str(READINESS_SCRIPT), "--plan", "configs/training_plan.example.yml"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "not_ready"
    assert payload["training_attempted"] is False


def test_training_readiness_refuses_allow_train_when_not_ready() -> None:
    result = subprocess.run(
        [sys.executable, str(READINESS_SCRIPT), "--plan", "configs/training_plan.example.yml", "--allow-train"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["allow_train_result"] == "refused"
    assert payload["training_attempted"] is False


def test_synthetic_smoke_training_requires_allow_train() -> None:
    result = subprocess.run(
        [sys.executable, str(SMOKE_SCRIPT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "dry_run"
    assert payload["training_attempted"] is False


def test_synthetic_smoke_training_writes_only_tmp(tmp_path: Path) -> None:
    out = Path("/tmp/signal_engine_smoke_training/test_baseline_smoke_metrics.json")
    if out.exists():
        out.unlink()
    result = subprocess.run(
        [sys.executable, str(SMOKE_SCRIPT), "--allow-train", "--out", str(out)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["status"] == "synthetic_smoke_only"
    assert payload["output_policy"] == "no_model_weights_committed"

    blocked = subprocess.run(
        [sys.executable, str(SMOKE_SCRIPT), "--allow-train", "--out", str(tmp_path / "metrics.json")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert blocked.returncode == 2
    assert "under /tmp" in blocked.stderr
