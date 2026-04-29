from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "train_signal_baseline.py"


def test_multimodal_wrapper_baseline_reports_transcript_only_scaffold(tmp_path: Path) -> None:
    out_dir = tmp_path / "multimodal_research"
    report_path = tmp_path / "signal_baseline_report.md"
    subprocess.run(
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
    )

    status = json.loads((out_dir / "baseline_status.json").read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")

    assert status["transcript_only"] is True
    assert status["multimodal_training_ready"] is False
    assert "transcript-only" in report


def test_multimodal_wrapper_baseline_can_train_on_toy_examples(tmp_path: Path) -> None:
    examples_path = tmp_path / "toy_examples.jsonl"
    out_dir = tmp_path / "multimodal_research"
    report_path = tmp_path / "signal_baseline_report.md"

    rows = [
        {"text": "pricing is too high and finance may escalate", "label": "risk_friction"},
        {"text": "the competitor quote is lower and procurement is blocked", "label": "risk_friction"},
        {"text": "i will send the renewal plan and confirm owners today", "label": "opportunity_commitment"},
        {"text": "we can move to procurement next week if security signs off", "label": "opportunity_commitment"},
        {"text": "visibility is limited and the timeline may slip", "label": "uncertainty_hedging"},
        {"text": "for now we are not sure whether the rollout lands on time", "label": "uncertainty_hedging"},
        {"text": "sharing the current status for reference", "label": "neutral"},
        {"text": "the meeting starts tomorrow and the note is attached", "label": "neutral"},
        {"text": "support still has not resolved the issue and the dispute may escalate", "label": "risk_friction"},
        {"text": "we will send the security packet and discount range", "label": "opportunity_commitment"},
        {"text": "the forecast could change because visibility is unclear", "label": "uncertainty_hedging"},
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

    status = json.loads((out_dir / "baseline_status.json").read_text(encoding="utf-8"))
    metrics = json.loads((out_dir / "baseline_metrics.json").read_text(encoding="utf-8"))

    assert status["status"] == "ok"
    assert metrics["status"] == "ok"
    assert metrics["macro_f1"] >= 0.0
