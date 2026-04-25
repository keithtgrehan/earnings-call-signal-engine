from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "scripts" / "build_human_reviewed_signal_labels.py"
EVAL_SCRIPT = ROOT / "scripts" / "evaluate_signal_baseline.py"


def _load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_evaluate_signal_baseline_runs_on_seeded_dataset(tmp_path: Path) -> None:
    dataset_path = tmp_path / "human_reviewed_signal_labels.jsonl"
    metrics_path = tmp_path / "transcript_baseline_metrics.json"
    predictions_path = tmp_path / "transcript_baseline_predictions.jsonl"
    report_path = tmp_path / "transcript_baseline_benchmark.md"

    subprocess.run(
        [
            sys.executable,
            str(BUILD_SCRIPT),
            "--out",
            str(dataset_path),
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(EVAL_SCRIPT),
            "--input-path",
            str(dataset_path),
            "--metrics-path",
            str(metrics_path),
            "--predictions-path",
            str(predictions_path),
            "--report-path",
            str(report_path),
        ],
        cwd=ROOT,
        check=True,
    )

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    predictions = _load_jsonl(predictions_path)
    report = report_path.read_text(encoding="utf-8")

    assert metrics["status"] == "ok"
    assert metrics["deterministic_rules"]["macro_f1"] >= 0.0
    assert metrics["classifier"]["macro_f1"] >= 0.0
    assert predictions
    assert "This is an early labeled benchmark, not statistical proof." in report
    assert "The classifier is a research benchmark only." in report
    assert "Deterministic rules remain canonical unless the benchmark proves otherwise." in report


def test_evaluate_signal_baseline_handles_insufficient_dataset(tmp_path: Path) -> None:
    dataset_path = tmp_path / "tiny_labels.jsonl"
    metrics_path = tmp_path / "transcript_baseline_metrics.json"
    predictions_path = tmp_path / "transcript_baseline_predictions.jsonl"
    report_path = tmp_path / "transcript_baseline_benchmark.md"

    rows = [
        {"id": "a", "source_file": "toy", "domain": "support", "text": "pricing is too high", "signal_family": "risk_friction", "label_source": "human_seeded_v1", "evidence_terms": ["pricing"], "rationale": "toy", "pii_redacted": False, "notes": ""},
        {"id": "b", "source_file": "toy", "domain": "sales", "text": "i will send the plan", "signal_family": "opportunity_commitment", "label_source": "human_seeded_v1", "evidence_terms": ["send"], "rationale": "toy", "pii_redacted": False, "notes": ""},
        {"id": "c", "source_file": "toy", "domain": "sales", "text": "we may slip", "signal_family": "uncertainty_hedging", "label_source": "human_seeded_v1", "evidence_terms": ["may"], "rationale": "toy", "pii_redacted": False, "notes": ""},
        {"id": "d", "source_file": "toy", "domain": "sales", "text": "the meeting starts at nine", "signal_family": "neutral", "label_source": "human_seeded_v1", "evidence_terms": ["meeting"], "rationale": "toy", "pii_redacted": False, "notes": ""},
    ]
    dataset_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )

    subprocess.run(
        [
            sys.executable,
            str(EVAL_SCRIPT),
            "--input-path",
            str(dataset_path),
            "--metrics-path",
            str(metrics_path),
            "--predictions-path",
            str(predictions_path),
            "--report-path",
            str(report_path),
        ],
        cwd=ROOT,
        check=True,
    )

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    predictions = predictions_path.read_text(encoding="utf-8")

    assert metrics["status"] == "insufficient_data"
    assert "too small or too imbalanced" in metrics["reason"]
    assert predictions == ""
