from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BUILD_LABELS = ROOT / "scripts" / "build_human_reviewed_signal_labels.py"
MINE_SCRIPT = ROOT / "scripts" / "mine_signal_label_candidates.py"
REPORT_SCRIPT = ROOT / "scripts" / "report_label_dataset_growth.py"


def test_report_label_dataset_growth_summarizes_current_counts(tmp_path: Path) -> None:
    labels_path = tmp_path / "human_reviewed_signal_labels.jsonl"
    review_csv_path = tmp_path / "signal_label_candidates_review.csv"
    json_out = tmp_path / "label_dataset_growth.json"
    report_out = tmp_path / "label-dataset-growth-report.md"

    subprocess.run([sys.executable, str(BUILD_LABELS), "--out", str(labels_path)], cwd=ROOT, check=True)
    subprocess.run(
        [
            sys.executable,
            str(MINE_SCRIPT),
            "--review-csv-out",
            str(review_csv_path),
            "--jsonl-out",
            str(tmp_path / "signal_label_candidates.jsonl"),
            "--report-out",
            str(tmp_path / "signal-label-candidate-mining.md"),
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(REPORT_SCRIPT),
            "--labels-path",
            str(labels_path),
            "--candidate-review-path",
            str(review_csv_path),
            "--json-out",
            str(json_out),
            "--report-out",
            str(report_out),
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["current_reviewed_label_count"] == 48
    assert payload["candidate_count"] >= 100
    assert payload["target_gaps"]["100_labels"] == 52
    assert "Local fixtures remain the primary training source" in report_out.read_text(encoding="utf-8")
