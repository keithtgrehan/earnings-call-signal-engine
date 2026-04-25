from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "import_second_review_labels.py"


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "id",
        "text",
        "current_label",
        "reviewer_label",
        "reviewer_confidence",
        "reviewer_notes",
        "evidence_terms",
        "rationale",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_import_second_review_labels_writes_blocked_template_when_blank(tmp_path: Path) -> None:
    input_csv = tmp_path / "review_packet.csv"
    output_csv = tmp_path / "second_review_template.csv"
    _write_csv(
        input_csv,
        [
            {
                "id": "row1",
                "text": "pricing is too high",
                "current_label": "risk_friction",
                "reviewer_label": "",
                "reviewer_confidence": "",
                "reviewer_notes": "",
                "evidence_terms": "pricing",
                "rationale": "toy",
            }
        ],
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--input-csv",
            str(input_csv),
            "--output-csv",
            str(output_csv),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["status"] == "blocked"
    assert output_csv.exists()


def test_import_second_review_labels_accepts_filled_reviewer_labels(tmp_path: Path) -> None:
    input_csv = tmp_path / "review_packet.csv"
    output_csv = tmp_path / "second_review_template.csv"
    _write_csv(
        input_csv,
        [
            {
                "id": "row1",
                "text": "pricing is too high",
                "current_label": "risk_friction",
                "reviewer_label": "risk_friction",
                "reviewer_confidence": "0.8",
                "reviewer_notes": "agree",
                "evidence_terms": "pricing",
                "rationale": "toy",
            }
        ],
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--input-csv",
            str(input_csv),
            "--output-csv",
            str(output_csv),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["status"] == "ready_for_agreement"
    assert payload["reviewer_label_count"] == 1
