from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_audio_pilot_assets.py"


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "id",
        "domain",
        "transcript_text",
        "expected_signal_family",
        "expected_review_action",
        "audio_file_to_add",
        "audio_start_seconds",
        "audio_end_seconds",
        "audio_rights_confirmed",
        "reviewer_notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_validate_audio_pilot_assets_returns_blocked_when_empty(tmp_path: Path) -> None:
    input_csv = tmp_path / "audio_pilot_intake.csv"
    status_out = tmp_path / "audio_pilot_asset_status.json"
    report_out = tmp_path / "audio_pilot_asset_status.md"
    _write_csv(
        input_csv,
        [
            {
                "id": "pilot1",
                "domain": "support",
                "transcript_text": "pricing is too high",
                "expected_signal_family": "risk_friction",
                "expected_review_action": "review",
                "audio_file_to_add": "",
                "audio_start_seconds": "",
                "audio_end_seconds": "",
                "audio_rights_confirmed": "",
                "reviewer_notes": "",
            }
        ],
    )

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--input-csv",
            str(input_csv),
            "--status-out",
            str(status_out),
            "--report-out",
            str(report_out),
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(status_out.read_text(encoding="utf-8"))
    assert payload["status"] == "blocked"
    assert "No aligned approved audio assets" in payload["reason"]


def test_validate_audio_pilot_assets_accepts_approved_existing_audio(tmp_path: Path) -> None:
    audio_file = tmp_path / "clip.wav"
    audio_file.write_bytes(b"RIFFfakeWAVE")
    input_csv = tmp_path / "audio_pilot_intake.csv"
    status_out = tmp_path / "audio_pilot_asset_status.json"
    report_out = tmp_path / "audio_pilot_asset_status.md"
    _write_csv(
        input_csv,
        [
            {
                "id": "pilot1",
                "domain": "support",
                "transcript_text": "pricing is too high",
                "expected_signal_family": "risk_friction",
                "expected_review_action": "review",
                "audio_file_to_add": str(audio_file),
                "audio_start_seconds": "1.0",
                "audio_end_seconds": "3.5",
                "audio_rights_confirmed": "yes",
                "reviewer_notes": "",
            }
        ],
    )

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--input-csv",
            str(input_csv),
            "--status-out",
            str(status_out),
            "--report-out",
            str(report_out),
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(status_out.read_text(encoding="utf-8"))
    assert payload["status"] == "ready_for_audio_feature_extraction"
    assert payload["usable_case_ids"] == ["pilot1"]
