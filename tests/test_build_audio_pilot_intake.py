from __future__ import annotations

import csv
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "build_audio_pilot_intake.py"


def test_build_audio_pilot_intake_outputs_blank_audio_columns(tmp_path: Path) -> None:
    out_path = tmp_path / "audio_pilot_intake.csv"
    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--out",
            str(out_path),
        ],
        cwd=ROOT,
        check=True,
    )

    with out_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert rows
    assert rows[0]["audio_file_to_add"] == ""
    assert rows[0]["audio_rights_confirmed"] == ""
