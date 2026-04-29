from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "evaluate_signal_outputs.py"


def run_evaluator(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_evaluator_counts_tiny_fixture(tmp_path: Path) -> None:
    report = tmp_path / "report.md"
    summary = tmp_path / "summary.json"

    result = run_evaluator(
        "--gold-labels",
        "data/gold_labels.example.jsonl",
        "--predictions",
        "tests/fixtures/tiny_signal_predictions.jsonl",
        "--report-out",
        str(report),
        "--json-out",
        str(summary),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(summary.read_text(encoding="utf-8"))
    assert payload == {
        "total_labels": 7,
        "matched_labels": 5,
        "unmatched_labels": 2,
        "potential_false_positives": 1,
        "missing_evidence": 1,
        "direction_mismatch": 1,
    }
    assert "Signal Output Evaluation" in report.read_text(encoding="utf-8")


def test_duplicate_predictions_count_extras_as_false_positives(tmp_path: Path) -> None:
    gold = tmp_path / "gold.jsonl"
    predictions = tmp_path / "predictions.jsonl"
    report = tmp_path / "report.md"
    summary = tmp_path / "summary.json"
    gold.write_text(
        json.dumps(
            {
                "case_id": "CASE_1",
                "signal_type": "guidance_revision",
                "direction": "positive",
                "evidence_text": "Raised outlook.",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    predictions.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "case_id": "CASE_1",
                        "signal_type": "guidance_revision",
                        "direction": "positive",
                        "evidence_text": "Raised outlook.",
                    }
                ),
                json.dumps(
                    {
                        "case_id": "CASE_1",
                        "signal_type": "guidance_revision",
                        "direction": "positive",
                        "evidence_text": "Duplicate signal.",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = run_evaluator(
        "--gold-labels",
        str(gold),
        "--predictions",
        str(predictions),
        "--report-out",
        str(report),
        "--json-out",
        str(summary),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(summary.read_text(encoding="utf-8"))
    assert payload["matched_labels"] == 1
    assert payload["potential_false_positives"] == 1
