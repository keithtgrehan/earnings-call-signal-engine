from __future__ import annotations

import csv
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "prioritize_label_candidates.py"


def test_prioritize_label_candidates_builds_30_row_packet(tmp_path: Path) -> None:
    csv_out = tmp_path / "candidate_review_priority_30.csv"
    report_out = tmp_path / "candidate-review-priority-30.md"

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--csv-out",
            str(csv_out),
            "--report-out",
            str(report_out),
        ],
        cwd=ROOT,
        check=True,
    )

    rows = list(csv.DictReader(csv_out.open("r", encoding="utf-8", newline="")))
    assert len(rows) == 30
    assert all(row["reviewer_label"] == "" for row in rows)
    assert all(row["accepted"] == "" for row in rows)
    assert any(row["suggested_label"] == "neutral" for row in rows)
    assert any(row["suggested_label"] == "risk_friction" for row in rows)
    assert any(row["suggested_label"] == "uncertainty_hedging" for row in rows)
    assert report_out.exists()
    assert "review queue" in report_out.read_text(encoding="utf-8").lower()
