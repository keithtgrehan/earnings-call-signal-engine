from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_event_study_cases.py"


def test_event_study_example_validates() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--path", "configs/event_study_cases.example.yml"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_event_study_validator_rejects_missing_controls_window_and_model(tmp_path: Path) -> None:
    payload = yaml.safe_load((ROOT / "configs" / "event_study_cases.example.yml").read_text(encoding="utf-8"))
    row = payload["event_study_cases"][0]
    row.pop("event_window")
    row.pop("estimation_window")
    row["expected_return_model"] = "unsupported_model"
    row["controls"] = {"market_return": "required"}
    path = tmp_path / "bad_event.yml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--path", str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "missing required field event_window" in result.stdout
    assert "missing required field estimation_window" in result.stdout
    assert "expected_return_model" in result.stdout
    assert "missing control earnings_surprise" in result.stdout


def test_event_study_validator_rejects_positive_unsafe_claims(tmp_path: Path) -> None:
    payload = yaml.safe_load((ROOT / "configs" / "event_study_cases.example.yml").read_text(encoding="utf-8"))
    payload["event_study_cases"][0]["claim_limitations"] = (
        "This produces statistically significant causal alpha and trading performance."
    )
    path = tmp_path / "unsafe_event.yml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--path", str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "unsafe event-study claim" in result.stdout
