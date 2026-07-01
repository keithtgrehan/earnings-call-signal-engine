from __future__ import annotations

from typing import Any

NEUTRAL_FEATURE_NAMES = {
    "pause_duration",
    "speech_rate",
    "filler_count",
    "pitch_f0_summary",
    "energy_summary",
    "asr_confidence",
    "diarization_confidence",
    "overlap_count",
}


def neutral_audio_feature_row(*, case_id: str, audio_sha256: str, feature_name: str, value: str = "") -> dict[str, Any]:
    if feature_name not in NEUTRAL_FEATURE_NAMES:
        raise ValueError(f"unsupported neutral audio feature: {feature_name}")
    return {
        "case_id": case_id,
        "audio_sha256": audio_sha256,
        "feature_name": feature_name,
        "value": value,
        "label_type": "neutral_metadata",
        "emotion_label": False,
        "deception_label": False,
        "stress_label": False,
        "biometric_label": False,
    }
