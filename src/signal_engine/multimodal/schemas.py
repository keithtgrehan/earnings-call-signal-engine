from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def _bounded_confidence(value: float) -> float:
    return round(max(0.0, min(0.95, float(value))), 4)


@dataclass(frozen=True)
class EvidenceSpan:
    text: str
    start_char: int
    end_char: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceWindow:
    start_seconds: float | None
    end_seconds: float | None
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SignalFeature:
    signal_name: str
    modality: str
    strength: str
    confidence: float
    reason: str
    recommended_review_action: str
    evidence_span: EvidenceSpan | None = None
    evidence_window: EvidenceWindow | None = None
    measurements: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["confidence"] = _bounded_confidence(self.confidence)
        if self.evidence_span is not None:
            payload["evidence_span"] = self.evidence_span.to_dict()
        if self.evidence_window is not None:
            payload["evidence_window"] = self.evidence_window.to_dict()
        return payload


@dataclass(frozen=True)
class ModalityFeatureSet:
    modality: str
    available: bool
    source_path: str | None = None
    measurements: dict[str, Any] = field(default_factory=dict)
    signals: list[SignalFeature] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    adapter_used: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["signals"] = [item.to_dict() for item in self.signals]
        return payload


@dataclass(frozen=True)
class FusedSignal:
    signal_name: str
    modalities: list[str]
    strength: str
    confidence: float
    reason: str
    recommended_review_action: str
    evidence_spans: list[EvidenceSpan] = field(default_factory=list)
    evidence_windows: list[EvidenceWindow] = field(default_factory=list)
    supporting_measurements: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["confidence"] = _bounded_confidence(self.confidence)
        payload["evidence_spans"] = [item.to_dict() for item in self.evidence_spans]
        payload["evidence_windows"] = [item.to_dict() for item in self.evidence_windows]
        return payload


@dataclass(frozen=True)
class MultimodalSignalReport:
    input_metadata: dict[str, Any]
    modality_feature_sets: dict[str, ModalityFeatureSet]
    fused_signals: list[FusedSignal]
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_metadata": dict(self.input_metadata),
            "modality_feature_sets": {
                key: value.to_dict() for key, value in self.modality_feature_sets.items()
            },
            "fused_signals": [item.to_dict() for item in self.fused_signals],
            "limitations": list(self.limitations),
        }


__all__ = [
    "EvidenceSpan",
    "EvidenceWindow",
    "FusedSignal",
    "ModalityFeatureSet",
    "MultimodalSignalReport",
    "SignalFeature",
]
