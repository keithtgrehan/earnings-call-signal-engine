from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .schemas import ConversationRecord


@dataclass(frozen=True)
class OptionalComponent:
    name: str
    enabled: bool
    required_for_canonical_scoring: bool
    purpose: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def optional_multimodal_components() -> list[OptionalComponent]:
    return [
        OptionalComponent(
            name="asr_transcription",
            enabled=False,
            required_for_canonical_scoring=False,
            purpose="Optional offline speech-to-text when the input is audio rather than transcript text.",
        ),
        OptionalComponent(
            name="speaker_diarization",
            enabled=False,
            required_for_canonical_scoring=False,
            purpose="Optional speaker separation before role mapping and per-speaker turn analysis.",
        ),
        OptionalComponent(
            name="audio_features",
            enabled=False,
            required_for_canonical_scoring=False,
            purpose="Optional prosody and pause features for later review workflows.",
        ),
        OptionalComponent(
            name="video_keyframes",
            enabled=False,
            required_for_canonical_scoring=False,
            purpose="Optional keyframe extraction for multimodal investigations, not canonical scoring.",
        ),
    ]


def build_multimodal_metadata(record: ConversationRecord) -> dict[str, Any]:
    return {
        "canonical_path": "text_first_offline",
        "audio_metadata_present": bool(record.audio_metadata),
        "video_metadata_present": bool(record.video_metadata),
        "optional_components": [item.to_dict() for item in optional_multimodal_components()],
    }
