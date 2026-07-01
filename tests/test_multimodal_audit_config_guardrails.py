from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "multimodal_audit.example.yaml"


def load_config() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def test_example_config_defaults_to_disabled() -> None:
    config = load_config()

    assert config["enabled"] is False
    assert config["transcript_only_default"] is True
    assert config["canonical_status"] == "reviewer_support_only"


def test_raw_audio_video_disabled_by_default() -> None:
    config = load_config()

    assert config["allow_raw_audio"] is False
    assert config["allow_raw_video"] is False


def test_rights_clearance_required() -> None:
    config = load_config()

    assert config["require_rights_clearance"] is True


def test_banned_outputs_include_core_guardrails() -> None:
    banned = set(load_config()["banned_outputs"])

    for field in [
        "emotion_label",
        "deception_score",
        "manipulation_score",
        "mental_health_label",
        "biometric_identity",
    ]:
        assert field in banned


def test_flagged_windows_only_true() -> None:
    config = load_config()

    assert config["flagged_windows_only"] is True
