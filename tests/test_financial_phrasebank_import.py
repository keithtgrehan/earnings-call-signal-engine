from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "import_financial_phrasebank.py"


def test_import_financial_phrasebank_normalizes_local_tsv(tmp_path: Path) -> None:
    input_dir = tmp_path / "external" / "financial_phrasebank"
    input_dir.mkdir(parents=True)
    (input_dir / "phrasebank.tsv").write_text(
        "sentence\tlabel\n"
        "Demand improved quarter over quarter\tpositive\n"
        "Guidance remained uncertain\tneutral\n"
        "Margins deteriorated on the cost side\tnegative\n",
        encoding="utf-8",
    )
    out_path = tmp_path / "financial_phrasebank_normalized.jsonl"
    report_path = tmp_path / "financial-phrasebank-benchmark.md"

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--input-dir",
            str(input_dir),
            "--out",
            str(out_path),
            "--report-out",
            str(report_path),
        ],
        cwd=ROOT,
        check=True,
    )

    rows = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 3
    assert all(row["benchmark_only"] is True for row in rows)
    assert {row["label"] for row in rows} == {"positive", "neutral", "negative"}
    assert "benchmark-only" in report_path.read_text(encoding="utf-8").lower()


def test_import_financial_phrasebank_blocks_cleanly_when_missing(tmp_path: Path) -> None:
    input_dir = tmp_path / "external" / "financial_phrasebank"
    input_dir.mkdir(parents=True)
    report_path = tmp_path / "financial-phrasebank-benchmark.md"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--input-dir",
            str(input_dir),
            "--report-out",
            str(report_path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["status"] == "blocked_missing_source"
    assert "Manual Steps" in report_path.read_text(encoding="utf-8")
