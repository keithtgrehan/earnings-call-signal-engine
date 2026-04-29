from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "train_text_classifier_baseline.py"


def run_trainer(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_trainer_help() -> None:
    result = run_trainer("--help")

    assert result.returncode == 0
    assert "local sklearn text baseline" in result.stdout


def test_missing_labels_fails_cleanly(tmp_path: Path) -> None:
    result = run_trainer("--labels", str(tmp_path / "missing.jsonl"))

    assert result.returncode != 0
    assert "--labels does not exist" in result.stderr


def test_optional_sklearn_smoke_train_or_skip(tmp_path: Path) -> None:
    labels = tmp_path / "labels.jsonl"
    report = tmp_path / "report.json"
    rows = [
        {"evidence_text": "We are raising our revenue outlook.", "signal_type": "guidance_revision"},
        {"evidence_text": "The recovery path remains uncertain.", "signal_type": "uncertainty"},
        {"evidence_text": "We are raising our full-year forecast.", "signal_type": "guidance_revision"},
        {"evidence_text": "Visibility remains limited.", "signal_type": "uncertainty"},
    ]
    labels.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    result = run_trainer("--labels", str(labels), "--report-out", str(report))

    assert result.returncode == 0, result.stdout + result.stderr
    assert report.exists()
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["validated"] is False
    assert payload["status"] in {"skipped", "trained_local_smoke_only"}
    assert payload.get("model_written", False) is False
