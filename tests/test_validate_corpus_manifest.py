from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_corpus_manifest.py"


def run_validator(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_valid_example_csv_passes() -> None:
    result = run_validator("--path", "data/corpus_manifest.example.csv")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "valid" in result.stdout


def test_valid_example_json_passes() -> None:
    result = run_validator("--path", "data/corpus_manifest.example.json")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "valid" in result.stdout


def test_missing_required_field_fails(tmp_path: Path) -> None:
    source = ROOT / "data" / "corpus_manifest.example.csv"
    rows = list(csv.DictReader(source.open(newline="", encoding="utf-8")))
    fieldnames = [name for name in rows[0].keys() if name != "case_id"]
    broken = tmp_path / "missing_case_id.csv"
    with broken.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({key: rows[0][key] for key in fieldnames})

    result = run_validator("--path", str(broken))

    assert result.returncode == 1
    assert "missing required field case_id" in result.stdout


def test_json_summary_reports_row_count(tmp_path: Path) -> None:
    summary = tmp_path / "summary.json"

    result = run_validator(
        "--path",
        "data/corpus_manifest.example.json",
        "--json-out",
        str(summary),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(summary.read_text(encoding="utf-8"))
    assert payload["status"] == "valid"
    assert payload["row_count"] == 8
