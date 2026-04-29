from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .domains import ROLE_ALIASES, SUPPORTED_DOMAINS

SCHEMA_VERSION = "signal_engine_2.0"


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split()).strip()


def _normalize_role(value: Any) -> str:
    normalized = _normalize_text(value).lower().replace("-", "_").replace(" ", "_")
    if not normalized:
        return "unknown"
    return ROLE_ALIASES.get(normalized, normalized)


@dataclass(frozen=True)
class Participant:
    participant_id: str
    role: str
    name: str | None = None
    organization: str | None = None


@dataclass(frozen=True)
class TranscriptSegment:
    message_index: int
    role: str
    text: str
    speaker_id: str | None = None
    timestamp_start: str | None = None
    timestamp_end: str | None = None


@dataclass(frozen=True)
class Evidence:
    signal_name: str
    message_index: int | None
    matched_text: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConversationRecord:
    domain: str
    conversation_id: str
    participants: list[Participant]
    transcript_segments: list[TranscriptSegment]
    audio_metadata: dict[str, Any] = field(default_factory=dict)
    video_metadata: dict[str, Any] = field(default_factory=dict)
    source: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AnalysisResult:
    schema_version: str
    domain: str
    conversation_id: str
    scores: dict[str, float | int]
    risk_flags: list[str]
    opportunity_flags: list[str]
    evidence: list[Evidence]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence"] = [item.to_dict() for item in self.evidence]
        return payload


def _normalize_participants(
    raw_participants: Any,
    transcript_segments: list[TranscriptSegment],
) -> list[Participant]:
    participants: list[Participant] = []
    if isinstance(raw_participants, list):
        for index, item in enumerate(raw_participants):
            if not isinstance(item, dict):
                continue
            participant_id = _normalize_text(item.get("participant_id")) or f"participant_{index:02d}"
            participants.append(
                Participant(
                    participant_id=participant_id,
                    role=_normalize_role(item.get("role")),
                    name=_normalize_text(item.get("name")) or None,
                    organization=_normalize_text(item.get("organization")) or None,
                )
            )
    if participants:
        return participants

    inferred: dict[tuple[str | None, str], Participant] = {}
    for segment in transcript_segments:
        key = (segment.speaker_id, segment.role)
        if key not in inferred:
            inferred[key] = Participant(
                participant_id=segment.speaker_id or f"{segment.role}_{segment.message_index:02d}",
                role=segment.role,
                name=segment.speaker_id,
            )
    return list(inferred.values())


def _normalize_segments(raw_segments: Any) -> list[TranscriptSegment]:
    if not isinstance(raw_segments, list):
        raise ValueError("Conversation record must include a list of transcript segments or messages.")

    segments: list[TranscriptSegment] = []
    for index, item in enumerate(raw_segments):
        if not isinstance(item, dict):
            continue
        text = _normalize_text(item.get("text") or item.get("message") or item.get("content"))
        if not text:
            continue
        segments.append(
            TranscriptSegment(
                message_index=int(item.get("message_index", index)),
                role=_normalize_role(item.get("role") or item.get("speaker_role")),
                text=text,
                speaker_id=_normalize_text(
                    item.get("speaker_id") or item.get("participant_id") or item.get("speaker")
                )
                or None,
                timestamp_start=_normalize_text(item.get("timestamp_start") or item.get("start_time")) or None,
                timestamp_end=_normalize_text(item.get("timestamp_end") or item.get("end_time")) or None,
            )
        )
    return segments


def normalize_conversation_record(record: dict[str, Any], *, domain: str) -> ConversationRecord:
    if domain not in SUPPORTED_DOMAINS:
        raise ValueError(f"Unsupported domain: {domain!r}. Expected one of {SUPPORTED_DOMAINS}.")
    if not isinstance(record, dict):
        raise ValueError("Conversation record must be a JSON object.")

    conversation_id = _normalize_text(record.get("conversation_id") or record.get("call_id"))
    if not conversation_id:
        raise ValueError("Conversation record must include conversation_id or call_id.")

    raw_segments = record.get("transcript_segments")
    if raw_segments is None:
        raw_segments = record.get("messages")
    transcript_segments = _normalize_segments(raw_segments)
    if not transcript_segments:
        raise ValueError(f"Conversation {conversation_id} does not contain any transcript text.")

    participants = _normalize_participants(record.get("participants"), transcript_segments)
    source = record.get("source") or record.get("provenance") or {}
    audio_metadata = record.get("audio_metadata") or {}
    video_metadata = record.get("video_metadata") or {}

    return ConversationRecord(
        domain=domain,
        conversation_id=conversation_id,
        participants=participants,
        transcript_segments=transcript_segments,
        audio_metadata=dict(audio_metadata) if isinstance(audio_metadata, dict) else {},
        video_metadata=dict(video_metadata) if isinstance(video_metadata, dict) else {},
        source=dict(source) if isinstance(source, dict) else {},
    )
