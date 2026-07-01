from __future__ import annotations

from pathlib import Path

from signal_engine.audio.registry import validate_audio_registry_row


def test_audio_registry_rejects_commit_or_training_allowed() -> None:
    row = {
        "asset_type": "audio",
        "local_path": "/tmp/audio.mp3",
        "commit_allowed": "true",
        "training_allowed": "true",
        "eval_allowed": "true",
        "approval_ref": "",
    }

    errors = validate_audio_registry_row(row, repo_root=Path("/repo"))

    assert "commit_allowed must be false" in errors
    assert "training_allowed must be false" in errors
    assert "eval_allowed=true requires approval_ref" in errors
