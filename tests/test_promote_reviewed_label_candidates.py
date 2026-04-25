from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BUILD_LABELS = ROOT / "scripts" / "build_human_reviewed_signal_labels.py"
MINE_SCRIPT = ROOT / "scripts" / "mine_signal_label_candidates.py"
PROMOTE_SCRIPT = ROOT / "scripts" / "promote_reviewed_label_candidates.py"


def test_promote_reviewed_label_candidates_appends_only_accepted_rows(tmp_path: Path) -> None:
    labels_path = tmp_path / "human_reviewed_signal_labels.jsonl"
    review_csv_path = tmp_path / "signal_label_candidates_review.csv"
    status_out = tmp_path / "label_promotion_status.json"
    report_out = tmp_path / "label-promotion-status.md"

    subprocess.run([sys.executable, str(BUILD_LABELS), "--out", str(labels_path)], cwd=ROOT, check=True)
    subprocess.run(
        [
            sys.executable,
            str(MINE_SCRIPT),
            "--review-csv-out",
            str(review_csv_path),
            "--jsonl-out",
            str(tmp_path / "signal_label_candidates.jsonl"),
        ],
        cwd=ROOT,
        check=True,
    )

    rows = list(csv.DictReader(review_csv_path.open("r", encoding="utf-8", newline="")))
    rows[0]["accepted"] = "yes"
    rows[0]["reviewer_label"] = "neutral"
    rows[0]["reviewer_notes"] = "Looks like a safe neutral operational update."
    with review_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    subprocess.run(
        [
            sys.executable,
            str(PROMOTE_SCRIPT),
            "--review-csv-path",
            str(review_csv_path),
            "--labels-path",
            str(labels_path),
            "--status-out",
            str(status_out),
            "--report-out",
            str(report_out),
        ],
        cwd=ROOT,
        check=True,
    )

    updated_rows = [json.loads(line) for line in labels_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    status = json.loads(status_out.read_text(encoding="utf-8"))
    assert len(updated_rows) == 49
    assert status["promoted_rows"] == 1
    assert updated_rows[-1]["label_source"] == "human_reviewed_candidate_v1"
    assert report_out.exists()


def test_promote_reviewed_label_candidates_blocks_when_no_rows_accepted(tmp_path: Path) -> None:
    labels_path = tmp_path / "human_reviewed_signal_labels.jsonl"
    review_csv_path = tmp_path / "signal_label_candidates_review.csv"
    status_out = tmp_path / "label_promotion_status.json"

    subprocess.run([sys.executable, str(BUILD_LABELS), "--out", str(labels_path)], cwd=ROOT, check=True)
    subprocess.run(
        [
            sys.executable,
            str(MINE_SCRIPT),
            "--review-csv-out",
            str(review_csv_path),
            "--jsonl-out",
            str(tmp_path / "signal_label_candidates.jsonl"),
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(PROMOTE_SCRIPT),
            "--review-csv-path",
            str(review_csv_path),
            "--labels-path",
            str(labels_path),
            "--status-out",
            str(status_out),
            "--report-out",
            str(tmp_path / "report.md"),
        ],
        cwd=ROOT,
        check=True,
    )
    status = json.loads(status_out.read_text(encoding="utf-8"))
    assert status["status"] == "blocked_no_accepted_rows"
