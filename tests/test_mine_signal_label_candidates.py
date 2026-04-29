from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "mine_signal_label_candidates.py"


def test_mine_signal_label_candidates_creates_review_queue(tmp_path: Path) -> None:
    jsonl_out = tmp_path / "signal_label_candidates.jsonl"
    csv_out = tmp_path / "signal_label_candidates_review.csv"
    report_out = tmp_path / "signal-label-candidate-mining.md"

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--jsonl-out",
            str(jsonl_out),
            "--review-csv-out",
            str(csv_out),
            "--report-out",
            str(report_out),
        ],
        cwd=ROOT,
        check=True,
    )

    rows = [json.loads(line) for line in jsonl_out.read_text(encoding="utf-8").splitlines() if line.strip()]
    csv_rows = list(csv.DictReader(csv_out.open("r", encoding="utf-8", newline="")))
    assert len(rows) >= 100
    assert len(csv_rows) == len(rows)
    assert {row["suggested_label"] for row in rows} <= {
        "risk_friction",
        "opportunity_commitment",
        "uncertainty_hedging",
        "neutral",
    }
    assert any(row["suggested_label"] == "neutral" for row in rows)
    assert all(csv_row["reviewer_label"] == "" for csv_row in csv_rows)
    assert "review-queue builder" in report_out.read_text(encoding="utf-8").lower()
