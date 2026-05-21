from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_SCRIPT = ROOT / "scripts" / "validate_benchmark_registry.py"
BYOK_SCRIPT = ROOT / "scripts" / "validate_byok_reviewer_config.py"


def test_benchmark_registry_external_and_weak_labels_cannot_write_gold() -> None:
    result = subprocess.run(
        [sys.executable, str(BENCHMARK_SCRIPT), "--path", "configs/benchmark_registry.example.yml"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_benchmark_registry_rejects_external_gold_write(tmp_path: Path) -> None:
    payload = yaml.safe_load((ROOT / "configs" / "benchmark_registry.example.yml").read_text(encoding="utf-8"))
    payload["benchmarks"][2]["writes_gold"] = True
    path = tmp_path / "bad_benchmarks.yml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(BENCHMARK_SCRIPT), "--path", str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert "must not write gold" in result.stdout


def test_byok_output_role_cannot_be_canonical(tmp_path: Path) -> None:
    payload = yaml.safe_load((ROOT / "configs" / "byok_reviewer.example.yml").read_text(encoding="utf-8"))
    payload["output_role"] = "canonical"
    path = tmp_path / "bad_byok.yml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(BYOK_SCRIPT), "--path", str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert "reviewer or candidate" in result.stdout
