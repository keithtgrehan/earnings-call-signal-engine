"""Shared types and helpers for optional NLP sidecars."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from earnings_call_sentiment import optional_runtime

DEFAULT_BATCH_SIZE = 8
DEFAULT_MAX_LENGTH = 384
DEFAULT_MODEL_DEVICE = "auto"
SUPPORTED_UNIT_TYPES = ("chunks", "guidance_spans", "qa_answers")


@dataclass(frozen=True)
class TextUnit:
    case_id: str
    unit_type: str
    unit_id: str
    text: str
    source_artifact: str
    section: str | None = None
    speaker: str | None = None
    start_time_s: float | None = None
    end_time_s: float | None = None
    deterministic_label: str | None = None
    deterministic_score: float | None = None
    deterministic_signed_score: float | None = None
    deterministic_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LabelScore:
    label: str
    score: float
    rank: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ClassificationResult:
    unit: TextUnit
    scores: list[LabelScore]
    comparable_label: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EmbeddingResult:
    unit: TextUnit
    vector: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseSidecarModel(ABC):
    key = "base"
    model_id = ""
    output_kind = "unknown"

    def __init__(self, *, device: str = DEFAULT_MODEL_DEVICE, cache_dir: str | None = None) -> None:
        self.device = device
        self.cache_dir = cache_dir

    @abstractmethod
    def prewarm(self) -> dict[str, Any]:
        raise NotImplementedError


class BaseClassificationModel(BaseSidecarModel, ABC):
    output_kind = "classification"

    @abstractmethod
    def predict(
        self,
        units: list[TextUnit],
        *,
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_length: int = DEFAULT_MAX_LENGTH,
        label_groups: dict[str, list[str]] | None = None,
    ) -> list[ClassificationResult]:
        raise NotImplementedError


class BaseEmbeddingModel(BaseSidecarModel, ABC):
    output_kind = "embedding"

    @abstractmethod
    def embed(
        self,
        units: list[TextUnit],
        *,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> list[EmbeddingResult]:
        raise NotImplementedError


def _load_torch_module():
    return optional_runtime.load_optional_dependency("torch")


def resolve_runtime_device(requested: str) -> str:
    normalized = str(requested or DEFAULT_MODEL_DEVICE).strip().lower() or DEFAULT_MODEL_DEVICE
    if normalized in {"auto", "cuda"}:
        torch = _load_torch_module()
        if torch.cuda.is_available():
            return "cuda"
        if normalized == "cuda":
            raise RuntimeError(
                "CUDA was requested for NLP sidecars, but no CUDA device is available."
            )
        return "cpu"
    if normalized == "cpu":
        return "cpu"
    raise RuntimeError(
        f"Unsupported NLP sidecar device '{requested}'. Use 'auto', 'cpu', or 'cuda'."
    )


def pipeline_device_index(requested: str) -> int:
    return 0 if resolve_runtime_device(requested) == "cuda" else -1


def normalize_label(label: Any) -> str:
    return str(label or "").strip()


def normalize_polarity_label(label: str | None) -> str:
    lowered = normalize_label(label).lower()
    if "positive" in lowered:
        return "positive"
    if "negative" in lowered:
        return "negative"
    if "neutral" in lowered:
        return "neutral"
    return lowered or ""


def normalize_text_classification_scores(
    raw_output: Any,
    *,
    label_map: dict[str, str] | None = None,
    score_metadata: dict[str, Any] | None = None,
) -> list[LabelScore]:
    if isinstance(raw_output, dict):
        rows = [raw_output]
    elif isinstance(raw_output, list):
        rows = [item for item in raw_output if isinstance(item, dict)]
    else:
        rows = []

    normalized: list[LabelScore] = []
    for rank, row in enumerate(
        sorted(rows, key=lambda item: float(item.get("score", 0.0) or 0.0), reverse=True),
        start=1,
    ):
        raw_label = normalize_label(row.get("label"))
        label = label_map.get(raw_label, raw_label) if label_map else raw_label
        metadata = dict(score_metadata or {})
        normalized.append(
            LabelScore(
                label=label,
                score=round(float(row.get("score", 0.0) or 0.0), 6),
                rank=rank,
                metadata=metadata,
            )
        )
    return normalized
