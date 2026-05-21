from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "register_manual_local_files.py"


def test_manual_local_registration_does_not_copy_raw_content(tmp_path: Path) -> None:
    raw_file = tmp_path / "manual_transcript.txt"
    raw_file.write_text("PRIVATE RAW TRANSCRIPT CONTENT", encoding="utf-8")
    out = tmp_path / "registration.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--source-id",
            "manual_1",
            "--source-name",
            "Manual transcript",
            "--source-path",
            str(raw_file),
            "--media-type",
            "transcript",
            "--operator",
            "test",
            "--out",
            str(out),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    record = payload["records"][0]
    assert record["raw_file_copied_into_repo"] is False
    assert record["metadata_only"] is True
    assert record["source_url_or_path"] == str(raw_file)
    assert "PRIVATE RAW TRANSCRIPT CONTENT" not in out.read_text(encoding="utf-8")
