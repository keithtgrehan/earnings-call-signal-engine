from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

NORMALIZED_SCHEMA_VERSION = "multimodal_signal_engine.v1"

DOMAIN_ALIASES = {
    "earnings_call": "earnings",
    "earnings calls": "earnings",
    "finance": "earnings",
    "account_management": "sales",
    "renewals": "sales",
    "hr": "HR",
    "human_resources": "HR",
    "internal": "HR",
}

SUPPORTED_NORMALIZED_DOMAINS = ("earnings", "sales", "support", "HR", "general")


def normalize_domain(value: str | None) -> str:
    raw = str(value or "general").strip()
    if raw in SUPPORTED_NORMALIZED_DOMAINS:
        return raw
    lowered = raw.lower().replace("-", "_").replace(" ", "_")
    return DOMAIN_ALIASES.get(lowered, "general")


class Modality(str, Enum):
    text = "text"
    audio = "audio"
    video = "video"
    multimodal = "multimodal"


class Provenance(str, Enum):
    human_gold = "human_gold"
    weak = "weak"
    model = "model"
    synthetic = "synthetic"


class Timestamp(BaseModel):
    start: float | None = None
    end: float | None = None


class NormalizedRecord(BaseModel):
    schema_version: str = NORMALIZED_SCHEMA_VERSION
    id: str
    text: str = ""
    emotion: str | None = None
    sentiment: str | None = None
    domain: str = "general"
    source: str
    modality: Modality = Modality.text
    audio_path: str | None = None
    video_path: str | None = None
    timestamps: list[Timestamp] = Field(default_factory=list)
    provenance: Provenance = Provenance.weak
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        return _model_to_dict(self)


class SegmentRecord(BaseModel):
    schema_version: str = NORMALIZED_SCHEMA_VERSION
    segment_id: str
    record_id: str
    start_time: float | None = None
    end_time: float | None = None
    speaker: str = "unknown"
    text: str = ""
    domain: str = "general"
    source: str
    modality: Modality = Modality.text
    audio_path: str | None = None
    video_path: str | None = None
    provenance: Provenance = Provenance.weak
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        return _model_to_dict(self)


class DatasetIngestionStatus(BaseModel):
    dataset_id: str
    status: str
    source_path: str | None = None
    access: str = "unknown"
    modality: str = "text"
    loaded_rows: int = 0
    rejected_rows: int = 0
    checksum_sha256: str | None = None
    reason: str | None = None
    output_path: str | None = None

    def to_json_dict(self) -> dict[str, Any]:
        return _model_to_dict(self)


def path_if_exists(path: str | Path | None) -> str | None:
    if path is None:
        return None
    candidate = Path(path)
    return str(candidate) if candidate.exists() else None


def _model_to_dict(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    return model.dict()
