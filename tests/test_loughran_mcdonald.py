from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "import_loughran_mcdonald.py"


def test_import_loughran_mcdonald_imports_local_csv(tmp_path: Path) -> None:
    input_dir = tmp_path / "external" / "loughran_mcdonald"
    input_dir.mkdir(parents=True)
    source_path = input_dir / "Loughran-McDonald_MasterDictionary_1993-2024.csv"
    source_path.write_text(
        "Word,Negative,Positive,Uncertainty,Litigious,Weak_Modal,Strong_Modal,Constraining\n"
        "loss,1,0,0,0,0,0,0\n"
        "improve,0,1,0,0,0,0,0\n"
        "uncertain,0,0,1,0,0,0,0\n"
        "may,0,0,0,0,1,0,0\n"
        "lawsuit,0,0,0,1,0,0,0\n"
        "limit,0,0,0,0,0,0,1\n",
        encoding="utf-8",
    )
    json_out = tmp_path / "loughran_mcdonald_lexicon.json"
    report_out = tmp_path / "loughran-mcdonald-integration.md"

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--input-dir",
            str(input_dir),
            "--json-out",
            str(json_out),
            "--report-out",
            str(report_out),
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert "loss" in payload["negative"]
    assert "improve" in payload["positive"]
    assert "uncertain" in payload["uncertainty"]
    assert "may" in payload["modal"]
    assert "lawsuit" in payload["litigious"]
    assert "limit" in payload["constraining"]
    assert report_out.exists()


def test_import_loughran_mcdonald_blocks_cleanly_when_missing(tmp_path: Path) -> None:
    input_dir = tmp_path / "external" / "loughran_mcdonald"
    input_dir.mkdir(parents=True)
    report_out = tmp_path / "report.md"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--input-dir",
            str(input_dir),
            "--report-out",
            str(report_out),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["status"] == "blocked_missing_source"
    assert "Manual Steps" in report_out.read_text(encoding="utf-8")
