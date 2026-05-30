from __future__ import annotations

from pathlib import Path

from tools.validate_audio_registry import validate_registry


def test_audio_registry_validates_seed_manifest() -> None:
    summary = validate_registry(Path("data/acquisition/audio_registry.csv"))
    assert summary["rows"] == 1
    assert summary["errors"] == []
