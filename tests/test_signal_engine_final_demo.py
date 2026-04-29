from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "run_signal_engine_2_0_demo.py"


def test_signal_engine_final_demo_writes_expected_outputs(tmp_path: Path) -> None:
    out_dir = tmp_path / "final_demo"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--out-dir",
            str(out_dir),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["status"] == "ok"
    assert (out_dir / "support_output.json").exists()
    assert (out_dir / "sales_output.json").exists()
    assert (out_dir / "account_management_output.json").exists()
    assert (out_dir / "pii_redacted_support_output.json").exists()
    assert (out_dir / "text_emotion_benchmark" / "predictions.jsonl").exists()
    assert (out_dir / "text_emotion_benchmark" / "metrics.json").exists()
    assert (out_dir / "text_emotion_benchmark" / "report.md").exists()
    assert (out_dir / "text_emotion_benchmark" / "redactions.json").exists()

    demo_index = (out_dir / "demo_index.md").read_text(encoding="utf-8")
    assert "Signal Engine 2.0 Final Demo Index" in demo_index
    assert "benchmark macro f1" in demo_index.lower() or "macro f1" in demo_index.lower()
    assert "tiny handcrafted fixture" in demo_index
