from __future__ import annotations

import csv
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "build_label_review_packet.py"


def test_build_label_review_packet_outputs_csv_and_markdown(tmp_path: Path) -> None:
    csv_out = tmp_path / "signal_labels_review_packet.csv"
    markdown_out = tmp_path / "signal_labels_review_packet.md"

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--csv-out",
            str(csv_out),
            "--markdown-out",
            str(markdown_out),
        ],
        cwd=ROOT,
        check=True,
    )

    with csv_out.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    markdown = markdown_out.read_text(encoding="utf-8")

    assert rows
    assert rows[0]["current_label"] in {
        "risk_friction",
        "opportunity_commitment",
        "uncertainty_hedging",
        "neutral",
    }
    assert rows[0]["reviewer_label"] == ""
    assert "## risk_friction" in markdown
    assert "## opportunity_commitment" in markdown
