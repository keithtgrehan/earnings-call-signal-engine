from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_restricted_artifacts.py"


def test_vendor_transcript_source_blocked_for_raw_commit() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "data/vendor/raw/transcript.txt"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Restricted raw artifacts" in result.stderr


def test_restricted_artifact_checker_flags_audio_video_vendor_markers() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "data/vendor/raw/audio/call.mp3",
            "data/paywall/raw/video/call.mp4",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "call.mp3" in result.stderr
    assert "call.mp4" in result.stderr


def test_explicit_registry_permission_allows_raw_commit(tmp_path: Path) -> None:
    registry = {
        "resources": [
            {
                "source_id": "allowed_fixture",
                "source_name": "Allowed fixture",
                "source_url_or_path": "data/fixtures/raw/transcript.txt",
                "source_type": "synthetic_fixture",
                "rights_tier": "open_licensed",
                "license_or_terms_summary": "Synthetic fixture license allows raw body commit.",
                "allowed_storage": "raw_allowed_commit",
                "allowed_commit": True,
                "allowed_training_use": "yes",
                "allowed_eval_use": "yes",
                "raw_body_allowed": True,
                "metadata_only": False,
                "acquisition_method": "synthetic_fixture",
                "robots_or_terms_checked": True,
                "paywall_or_login_status": "public_no_login",
                "provenance_hash": "sha256:test",
                "last_checked_at": "2026-05-22",
                "reviewer_or_operator": "test",
                "blocked_reason": "",
                "notes": "",
            }
        ]
    }
    path = tmp_path / "registry.yml"
    path.write_text(yaml.safe_dump(registry), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--registry", str(path), "data/fixtures/raw/transcript.txt"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
