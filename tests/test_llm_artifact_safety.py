from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_llm_artifacts.py"


def _write(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_check_llm_artifacts_allows_missing_root(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path / "missing"), "--allow-missing"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_check_llm_artifacts_rejects_canonical_output_true(tmp_path: Path) -> None:
    artifact = tmp_path / "artifacts" / "llm" / "bad.json"
    _write(artifact, {"canonical_output": True, "output": {"canonical_output": False}})

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(artifact.parent)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "canonical_output" in result.stdout


def test_check_llm_artifacts_rejects_gold_label_write_markers(tmp_path: Path) -> None:
    artifact = tmp_path / "artifacts" / "llm" / "bad_gold.json"
    _write(artifact, {"canonical_output": False, "writes_gold": True})

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(artifact.parent)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "gold" in result.stdout.lower()


def test_check_llm_artifacts_rejects_secret_values(tmp_path: Path) -> None:
    secret = "sk-secret-value-should-not-appear"
    artifact = tmp_path / "artifacts" / "llm" / "bad_secret.json"
    _write(artifact, {"canonical_output": False, "message": secret})

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(artifact.parent)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    combined = result.stdout + result.stderr
    assert result.returncode == 1
    assert secret not in combined
    assert "[REDACTED]" in combined
