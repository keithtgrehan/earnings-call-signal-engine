from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "export_training_candidates.py"


def test_external_dataset_cannot_become_gold(tmp_path: Path) -> None:
    external = tmp_path / "external.jsonl"
    out = tmp_path / "out.json"
    external.write_text(json.dumps({"id": "external_1", "gold_label": "should_be_removed"}) + "\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--external", str(external), "--out", str(out)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    row = payload["external_benchmark_rows"][0]
    assert row["gold_eligible"] is False
    assert "gold_label" not in row
