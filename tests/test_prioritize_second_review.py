from __future__ import annotations

import csv
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BUILD_LABELS = ROOT / "scripts" / "build_human_reviewed_signal_labels.py"
EVAL_SCRIPT = ROOT / "scripts" / "evaluate_signal_baseline.py"
ERROR_SCRIPT = ROOT / "scripts" / "analyze_signal_errors.py"
HOLDOUT_SCRIPT = ROOT / "scripts" / "build_gold_holdout_set.py"
PRIORITY_SCRIPT = ROOT / "scripts" / "prioritize_second_review.py"


def test_prioritize_second_review_creates_blank_queue(tmp_path: Path) -> None:
    labels_path = tmp_path / "human_reviewed_signal_labels.jsonl"
    metrics_path = tmp_path / "transcript_baseline_metrics.json"
    predictions_path = tmp_path / "transcript_baseline_predictions.jsonl"
    benchmark_report = tmp_path / "transcript-baseline-benchmark.md"
    error_json = tmp_path / "signal_error_analysis.json"
    error_csv = tmp_path / "signal_error_analysis.csv"
    error_report = tmp_path / "signal-error-analysis.md"
    holdout_path = tmp_path / "gold_holdout_candidates.jsonl"
    queue_path = tmp_path / "second_review_priority_queue.csv"

    subprocess.run([sys.executable, str(BUILD_LABELS), "--out", str(labels_path)], cwd=ROOT, check=True)
    subprocess.run(
        [
            sys.executable,
            str(EVAL_SCRIPT),
            "--input-path",
            str(labels_path),
            "--metrics-path",
            str(metrics_path),
            "--predictions-path",
            str(predictions_path),
            "--report-path",
            str(benchmark_report),
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ERROR_SCRIPT),
            "--labels-path",
            str(labels_path),
            "--predictions-path",
            str(predictions_path),
            "--metrics-path",
            str(metrics_path),
            "--json-out",
            str(error_json),
            "--csv-out",
            str(error_csv),
            "--report-out",
            str(error_report),
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(HOLDOUT_SCRIPT),
            "--input-path",
            str(labels_path),
            "--out",
            str(holdout_path),
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(PRIORITY_SCRIPT),
            "--error-analysis-path",
            str(error_json),
            "--holdout-path",
            str(holdout_path),
            "--out",
            str(queue_path),
        ],
        cwd=ROOT,
        check=True,
    )

    rows = list(csv.DictReader(queue_path.open("r", encoding="utf-8", newline="")))
    assert 15 <= len(rows) <= 20
    assert all(row["reviewer_label"] == "" for row in rows)
    assert rows[0]["priority_reason"]
