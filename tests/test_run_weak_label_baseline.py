from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_weak_label_baseline.py"
EVALUATOR = ROOT / "scripts" / "evaluate_signal_outputs.py"


def load_jsonl(path: Path) -> list[dict[str, str]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run_baseline(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_weak_label_baseline_matches_expected_fixture(tmp_path: Path) -> None:
    out = tmp_path / "predictions.jsonl"

    result = run_baseline(
        "--input",
        "tests/fixtures/tiny_realistic_earnings_excerpt.txt",
        "--case-id",
        "TEST_2026_Q1",
        "--out",
        str(out),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert load_jsonl(out) == load_jsonl(ROOT / "tests/fixtures/tiny_weak_baseline_expected.jsonl")
    assert "not validated training data or real ML" in result.stdout


def test_weak_label_output_is_evaluator_compatible(tmp_path: Path) -> None:
    predictions = tmp_path / "predictions.jsonl"
    report = tmp_path / "report.md"
    summary = tmp_path / "summary.json"
    run_baseline(
        "--input",
        "tests/fixtures/tiny_realistic_earnings_excerpt.txt",
        "--case-id",
        "TEST_2026_Q1",
        "--out",
        str(predictions),
    )

    result = subprocess.run(
        [
            sys.executable,
            str(EVALUATOR),
            "--gold-labels",
            "data/gold_labels.example.jsonl",
            "--predictions",
            str(predictions),
            "--report-out",
            str(report),
            "--json-out",
            str(summary),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert report.exists()
    assert summary.exists()


def test_missing_input_fails_cleanly(tmp_path: Path) -> None:
    result = run_baseline("--input", str(tmp_path / "missing.txt"), "--case-id", "CASE", "--out", str(tmp_path / "out.jsonl"))

    assert result.returncode != 0
    assert "--input does not exist" in result.stderr
