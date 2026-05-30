from __future__ import annotations

from signal_engine.audio.schemas import AUDIO_REGISTRY_FIELDS, validate_no_forbidden_audio_labels


def test_audio_registry_schema_has_commit_guards() -> None:
    assert "raw_audio_committed" in AUDIO_REGISTRY_FIELDS
    assert "raw_asr_committed" in AUDIO_REGISTRY_FIELDS


def test_forbidden_audio_labels_are_rejected() -> None:
    errors = validate_no_forbidden_audio_labels({"emotion": "happy", "case_id": "vz_2024_q4"})
    assert errors == ["forbidden audio label field emotion"]
