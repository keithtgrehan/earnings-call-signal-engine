from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_gold_labels.py"


def run_validator(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_valid_example_jsonl_passes() -> None:
    result = run_validator("--path", "data/gold_labels.example.jsonl")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "valid" in result.stdout


def test_invalid_enum_fails(tmp_path: Path) -> None:
    row = {
        "case_id": "BAD_2026_Q1",
        "label_id": "BAD_2026_Q1_001",
        "signal_type": "not_a_signal",
        "direction": "negative",
        "speaker_role": "management",
        "evidence_text": "This row should fail enum validation.",
        "evidence_start": None,
        "evidence_end": None,
        "confidence": "medium",
        "notes": "Invalid enum fixture.",
    }
    path = tmp_path / "bad_enum.jsonl"
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    result = run_validator("--path", str(path))

    assert result.returncode == 1
    assert "invalid signal_type" in result.stdout


def test_missing_evidence_text_for_non_neutral_fails(tmp_path: Path) -> None:
    row = {
        "case_id": "BAD_2026_Q1",
        "label_id": "BAD_2026_Q1_002",
        "signal_type": "uncertainty",
        "direction": "negative",
        "speaker_role": "management",
        "evidence_text": "",
        "evidence_start": None,
        "evidence_end": None,
        "confidence": "medium",
        "notes": "Non-neutral evidence cannot be empty.",
    }
    path = tmp_path / "missing_evidence.jsonl"
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    result = run_validator("--path", str(path))

    assert result.returncode == 1
    assert "evidence_text is required for non-neutral labels" in result.stdout
