from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "signal_engine_analyze.py"
FIXTURE_PATH = ROOT / "data" / "signal_engine_2_0" / "fixtures" / "support_tickets_realistic.jsonl"


def test_signal_engine_analyze_redacts_pii_and_reports_summary() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--domain",
            "support",
            "--redact-pii",
            str(FIXTURE_PATH),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)

    serialized = json.dumps(payload, ensure_ascii=False)
    assert payload["metadata"]["pii_redaction"]["enabled"] is True
    assert payload["metadata"]["pii_redaction"]["summary"]["total_redactions"] >= 2
    assert "dana.ops@northwind.example" not in serialized
    assert "+1 415 555 0177" not in serialized
    assert any(flag.startswith("support_") for flag in payload["risk_flags"])
