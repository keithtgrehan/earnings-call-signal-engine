from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "train_signal_text_baseline.py"


def test_text_baseline_handles_insufficient_local_weak_labels(tmp_path: Path) -> None:
    out_dir = tmp_path / "nlp_research"
    report_path = tmp_path / "nlp_baseline_report.md"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--out-dir",
            str(out_dir),
            "--report-path",
            str(report_path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    metrics = json.loads((out_dir / "baseline_metrics.json").read_text(encoding="utf-8"))
    predictions = (out_dir / "baseline_predictions.jsonl").read_text(encoding="utf-8")
    report = report_path.read_text(encoding="utf-8")

    assert json.loads(completed.stdout)["status"] == "insufficient_data"
    assert metrics["status"] == "insufficient_data"
    assert metrics["task"] == "signal_family"
    assert "weak-label corpus" in metrics["reason"]
    assert predictions == ""
    assert "research benchmark only" in report


def test_text_baseline_trains_on_toy_labeled_examples(tmp_path: Path) -> None:
    examples_path = tmp_path / "toy_examples.jsonl"
    out_dir = tmp_path / "nlp_research"
    report_path = tmp_path / "nlp_baseline_report.md"

    rows = [
        {"text": "pricing is too high and we may escalate this week", "label": "risk_friction"},
        {"text": "the competitor quote is lower and procurement is blocked", "label": "risk_friction"},
        {"text": "please confirm owners and send the renewal plan today", "label": "opportunity_commitment"},
        {"text": "we can bring procurement in next week if the pilot looks good", "label": "opportunity_commitment"},
        {"text": "we might need more time because visibility is limited", "label": "uncertainty_hedging"},
        {"text": "for now the timeline may slip and the outlook is unclear", "label": "uncertainty_hedging"},
        {"text": "sharing the update and current status for reference", "label": "neutral"},
        {"text": "the meeting starts tomorrow and the attached note is for reference", "label": "neutral"},
        {"text": "this issue is still unresolved and finance will dispute the charge", "label": "risk_friction"},
        {"text": "i will send the action plan and confirm owners by friday", "label": "opportunity_commitment"},
        {"text": "we are not sure whether the quarter closes on time", "label": "uncertainty_hedging"},
        {"text": "the current status is unchanged and noted", "label": "neutral"},
    ]
    examples_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--examples-path",
            str(examples_path),
            "--out-dir",
            str(out_dir),
            "--report-path",
            str(report_path),
        ],
        cwd=ROOT,
        check=True,
    )

    metrics = json.loads((out_dir / "baseline_metrics.json").read_text(encoding="utf-8"))
    predictions = [
        json.loads(line)
        for line in (out_dir / "baseline_predictions.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    report = report_path.read_text(encoding="utf-8")

    assert metrics["status"] == "ok"
    assert metrics["model"] == "tfidf_logistic_regression"
    assert metrics["macro_f1"] >= 0.0
    assert predictions
    assert "Per-Label Metrics" in report
