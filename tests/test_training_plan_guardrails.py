from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_training_plan.py"


def test_training_plan_reports_not_ready_for_current_real_gold() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--path", "configs/training_plan.example.yml"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "NOT_READY" in result.stdout
    assert "gold labels do not pass validation" in result.stdout


def test_training_plan_rejects_external_dataset_gold_source(tmp_path: Path) -> None:
    payload = yaml.safe_load((ROOT / "configs" / "training_plan.example.yml").read_text(encoding="utf-8"))
    payload["allowed_sources"] = [{"source_kind": "external_dataset", "rights_tier": "open_licensed", "training_allowed": True}]
    path = tmp_path / "bad_training_plan.yml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--path", str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "external_dataset" in result.stdout


def test_training_plan_rejects_unknown_rights_when_training_enabled(tmp_path: Path) -> None:
    payload = yaml.safe_load((ROOT / "configs" / "training_plan.example.yml").read_text(encoding="utf-8"))
    payload["training_enabled"] = True
    payload["allowed_sources"] = [{"source_kind": "manual_review", "rights_tier": "unknown", "training_allowed": True}]
    path = tmp_path / "bad_rights_training_plan.yml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--path", str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "blocked rights_tier unknown" in result.stdout


def test_training_plan_dependency_and_database_policy_fail_closed(tmp_path: Path) -> None:
    payload = yaml.safe_load((ROOT / "configs" / "training_plan.example.yml").read_text(encoding="utf-8"))
    payload["dependency_policy"]["new_dependencies_allowed"] = True
    payload["database_policy"]["managed_databases"] = "allowed"
    path = tmp_path / "bad_dependency_plan.yml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--path", str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "new_dependencies_allowed must be false" in result.stdout
    assert "managed_databases must be blocked" in result.stdout
