from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LABEL_BUILD_SCRIPT = ROOT / "scripts" / "build_human_reviewed_signal_labels.py"
PILOT_BUILD_SCRIPT = ROOT / "scripts" / "build_multimodal_pilot_cases.py"
PILOT_EVAL_SCRIPT = ROOT / "scripts" / "evaluate_multimodal_pilot.py"


def test_evaluate_multimodal_pilot_reports_scaffold_only(tmp_path: Path) -> None:
    labels_path = ROOT / "data" / "nlp_research" / "human_reviewed_signal_labels.jsonl"
    if not labels_path.exists():
        subprocess.run(
            [sys.executable, str(LABEL_BUILD_SCRIPT)],
            cwd=ROOT,
            check=True,
        )

    cases_path = tmp_path / "multimodal_pilot_cases.jsonl"
    status_path = tmp_path / "multimodal_pilot_status.json"
    report_path = tmp_path / "multimodal_pilot_status.md"

    subprocess.run(
        [
            sys.executable,
            str(PILOT_BUILD_SCRIPT),
            "--out",
            str(cases_path),
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(PILOT_EVAL_SCRIPT),
            "--input-path",
            str(cases_path),
            "--status-path",
            str(status_path),
            "--report-path",
            str(report_path),
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(status_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")

    assert payload["status"] == "scaffold_only"
    assert payload["can_measure_multimodal_lift"] is False
    assert payload["cases_with_audio"] == 0
    assert payload["cases_with_video"] == 0
    assert "cannot be measured honestly" in payload["blocker"]
    assert "Multimodal Pilot Status" in report
