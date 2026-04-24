from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .multimodal_placeholders import build_multimodal_metadata
from .risk_rules import analyze_domain
from .schemas import AnalysisResult, SCHEMA_VERSION, normalize_conversation_record


def _load_records(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and isinstance(payload.get("conversations"), list):
            return [item for item in payload["conversations"] if isinstance(item, dict)]
        if isinstance(payload, dict):
            return [payload]
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        raise ValueError(f"Unsupported JSON structure in {path}.")
    if suffix == ".jsonl":
        records: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            item = json.loads(stripped)
            if isinstance(item, dict):
                records.append(item)
        return records
    raise ValueError(f"Unsupported file type: {path.suffix}. Use JSON or JSONL.")


def analyze_conversation_record(record: dict[str, Any], *, domain: str) -> dict[str, Any]:
    conversation = normalize_conversation_record(record, domain=domain)
    analysis = analyze_domain(conversation)
    metadata = {
        "participant_count": len(conversation.participants),
        "transcript_segment_count": len(conversation.transcript_segments),
        "source": conversation.source,
        "audio_metadata": conversation.audio_metadata,
        "video_metadata": conversation.video_metadata,
        "deterministic": True,
        "external_api_required": False,
        "llm_required_for_canonical_scoring": False,
        "built_now": [
            "deterministic transcript analysis",
            "domain-specific lexicon and role rules",
            "offline unified JSON output",
        ],
        "roadmap": [
            "optional ASR",
            "optional diarization",
            "optional audio features",
            "optional video keyframes",
            "optional retrieval and long-context review",
        ],
    }
    metadata.update(build_multimodal_metadata(conversation))
    result = AnalysisResult(
        schema_version=SCHEMA_VERSION,
        domain=conversation.domain,
        conversation_id=conversation.conversation_id,
        scores=analysis["scores"],
        risk_flags=analysis["risk_flags"],
        opportunity_flags=analysis["opportunity_flags"],
        evidence=analysis["evidence"],
        metadata=metadata,
    )
    return result.to_dict()


def analyze_path(path: str | Path, *, domain: str) -> list[dict[str, Any]]:
    file_path = Path(path)
    return [analyze_conversation_record(record, domain=domain) for record in _load_records(file_path)]
