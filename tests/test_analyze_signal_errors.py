from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "scripts" / "build_human_reviewed_signal_labels.py"
EVAL_SCRIPT = ROOT / "scripts" / "evaluate_signal_baseline.py"
ERROR_SCRIPT = ROOT / "scripts" / "analyze_signal_errors.py"


def test_analyze_signal_errors_generates_summary_and_review_queue(tmp_path: Path) -> None:
    labels_path = tmp_path / "human_reviewed_signal_labels.jsonl"
    metrics_path = tmp_path / "transcript_baseline_metrics.json"
    predictions_path = tmp_path / "transcript_baseline_predictions.jsonl"
    report_path = tmp_path / "transcript-baseline-benchmark.md"
    error_json = tmp_path / "signal_error_analysis.json"
    error_csv = tmp_path / "signal_error_analysis.csv"
    error_report = tmp_path / "signal-error-analysis.md"

    subprocess.run([sys.executable, str(BUILD_SCRIPT), "--out", str(labels_path)], cwd=ROOT, check=True)
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
            str(report_path),
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

    payload = json.loads(error_json.read_text(encoding="utf-8"))
    rows = list(csv.DictReader(error_csv.open("r", encoding="utf-8", newline="")))
    report = error_report.read_text(encoding="utf-8")

    assert payload["status"] == "ok"
    assert payload["error_buckets"]["counts"]["total_evaluated"] == len(rows)
    assert "## Headline Error Counts" in report
    assert rows[0]["error_bucket"]
