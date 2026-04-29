from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "build_public_resource_fit_manifest.py"


def test_public_resource_fit_manifest_builds_json_and_markdown(tmp_path: Path) -> None:
    manifest_out = tmp_path / "public_resource_fit_manifest.json"
    report_out = tmp_path / "public-resource-fit-report.md"

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--manifest-out",
            str(manifest_out),
            "--report-out",
            str(report_out),
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(manifest_out.read_text(encoding="utf-8"))
    report = report_out.read_text(encoding="utf-8")

    assert payload["status"] == "ok"
    assert payload["resource_count"] == 8
    assert payload["resources"][0]["fit_score_1_to_10"] >= payload["resources"][-1]["fit_score_1_to_10"]
    assert "## Ranking Table" in report
    assert "## What Not To Do" in report
