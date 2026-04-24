from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "extract_multimodal_features.py"


def test_extract_multimodal_features_cli_writes_text_only_report(tmp_path: Path) -> None:
    text_path = tmp_path / "note.txt"
    out_path = tmp_path / "multimodal_report.json"
    text_path.write_text(
        "Please update dana.ops@northwind.example today. We may slip this week and the team will escalate if billing stays unresolved.",
        encoding="utf-8",
    )

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--text-file",
            str(text_path),
            "--domain",
            "support",
            "--redact-pii",
            "--out",
            str(out_path),
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["input_metadata"]["pii_redaction"]["enabled"] is True
    assert payload["modality_feature_sets"]["transcript"]["available"] is True
    assert payload["fused_signals"]
