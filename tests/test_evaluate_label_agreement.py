from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "evaluate_label_agreement.py"


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


def test_evaluate_label_agreement_returns_blocked_when_no_labels(tmp_path: Path) -> None:
    input_csv = tmp_path / "second_review_template.csv"
    status_out = tmp_path / "label_agreement_status.json"
    report_out = tmp_path / "label_agreement_status.md"
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

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--input-csv",
            str(input_csv),
            "--status-out",
            str(status_out),
            "--report-out",
            str(report_out),
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(status_out.read_text(encoding="utf-8"))
    report = report_out.read_text(encoding="utf-8")
    assert payload["status"] == "blocked"
    assert "cannot be measured yet" in report


def test_evaluate_label_agreement_computes_metrics_when_labels_exist(tmp_path: Path) -> None:
    input_csv = tmp_path / "second_review_template.csv"
    status_out = tmp_path / "label_agreement_status.json"
    report_out = tmp_path / "label_agreement_status.md"
    _write_csv(
        input_csv,
        [
            {"id": "a", "text": "pricing is too high", "current_label": "risk_friction", "reviewer_label": "risk_friction", "reviewer_confidence": "0.8", "reviewer_notes": "", "evidence_terms": "pricing", "rationale": "toy"},
            {"id": "b", "text": "we may slip", "current_label": "uncertainty_hedging", "reviewer_label": "uncertainty_hedging", "reviewer_confidence": "0.7", "reviewer_notes": "", "evidence_terms": "may", "rationale": "toy"},
            {"id": "c", "text": "i will send the plan", "current_label": "opportunity_commitment", "reviewer_label": "risk_friction", "reviewer_confidence": "0.6", "reviewer_notes": "", "evidence_terms": "send", "rationale": "toy"},
            {"id": "d", "text": "the meeting starts at nine", "current_label": "neutral", "reviewer_label": "neutral", "reviewer_confidence": "0.9", "reviewer_notes": "", "evidence_terms": "meeting", "rationale": "toy"},
        ],
    )

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--input-csv",
            str(input_csv),
            "--status-out",
            str(status_out),
            "--report-out",
            str(report_out),
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(status_out.read_text(encoding="utf-8"))
    assert payload["status"] == "ok"
    assert payload["reviewed_example_count"] == 4
    assert payload["raw_agreement_percent"] == 75.0
    assert payload["disagreement_count"] == 1
    assert payload["per_class_disagreement_counts"]["opportunity_commitment"] == 1
