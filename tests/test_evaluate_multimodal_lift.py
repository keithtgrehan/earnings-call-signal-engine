from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "evaluate_multimodal_lift.py"


def test_evaluate_multimodal_lift_writes_scaffold_outputs(tmp_path: Path) -> None:
    status_out = tmp_path / "evaluation_status.json"
    protocol_out = tmp_path / "multimodal_evaluation_protocol.md"

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--status-out",
            str(status_out),
            "--protocol-out",
            str(protocol_out),
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(status_out.read_text(encoding="utf-8"))
    protocol = protocol_out.read_text(encoding="utf-8")

    assert payload["status"] == "scaffold_only"
    assert payload["transcript_only_canonical"] is True
    assert "Multimodal Evaluation Protocol" in protocol
