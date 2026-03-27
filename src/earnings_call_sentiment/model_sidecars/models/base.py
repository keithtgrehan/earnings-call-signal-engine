"""Shared types and helpers for optional model sidecars."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from earnings_call_sentiment import optional_runtime

DEFAULT_BATCH_SIZE = 8
DEFAULT_MAX_LENGTH = 512
DEFAULT_MODEL_DEVICE = "auto"
SUPPORTED_UNIT_TYPES = (
    "chunks",
    "guidance_spans",
    "qa_answers",
    "speaker_turns",
)


@dataclass(frozen=True)
class TextUnit:
    case_id: str
    unit_type: str
    source_id: str
    text: str
    section: str | None = None
    speaker: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LabelScore:
    label: str
    score: float
    rank: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ClassificationOutput:
    unit: TextUnit
    scores: list[LabelScore]


@dataclass(frozen=True)
class EmbeddingOutput:
    unit: TextUnit
    vector: list[float]


class BaseModelSidecar(ABC):
    """Base class for additive optional model sidecars."""

    key = "base"
    model_id = ""
    output_kind = "unknown"

    def __init__(self, *, device: str = DEFAULT_MODEL_DEVICE) -> None:
        self.device = device

    @abstractmethod
    def prewarm(self) -> dict[str, Any]:
        """Resolve optional dependencies and initialize the model runtime."""


class BaseClassificationSidecar(BaseModelSidecar, ABC):
    output_kind = "classification"

    @abstractmethod
    def predict(
        self,
        units: list[TextUnit],
        *,
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_length: int = DEFAULT_MAX_LENGTH,
        label_groups: dict[str, list[str]] | None = None,
    ) -> list[ClassificationOutput]:
        raise NotImplementedError


class BaseEmbeddingSidecar(BaseModelSidecar, ABC):
    output_kind = "embedding"

    @abstractmethod
    def embed(
        self,
        units: list[TextUnit],
        *,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> list[EmbeddingOutput]:
        raise NotImplementedError

    @abstractmethod
    def encode_texts(
        self,
        texts: list[str],
        *,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> list[list[float]]:
        raise NotImplementedError


def _clean_label(label: Any) -> str:
    return str(label or "").strip()


def _load_torch_module():
    return optional_runtime.load_optional_dependency("torch")


def resolve_runtime_device(requested: str) -> str:
    normalized = str(requested or "auto").strip().lower() or "auto"
    if normalized in {"auto", "cuda"}:
        torch = _load_torch_module()
        if torch.cuda.is_available():
            return "cuda"
        if normalized == "cuda":
            raise RuntimeError(
                "CUDA was requested for model sidecars, but no CUDA device is available."
            )
        return "cpu"
    if normalized == "cpu":
        return "cpu"
    raise RuntimeError(
        f"Unsupported model-sidecar device '{requested}'. Use 'auto', 'cpu', or 'cuda'."
    )


def pipeline_device_index(requested: str) -> int:
    return 0 if resolve_runtime_device(requested) == "cuda" else -1


def normalize_text_classification_scores(
    raw_output: Any,
    *,
    label_map: dict[str, str] | None = None,
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
        raw_label = _clean_label(row.get("label"))
        label = label_map.get(raw_label, raw_label) if label_map else raw_label
        normalized.append(
            LabelScore(
                label=label,
                score=round(float(row.get("score", 0.0) or 0.0), 6),
                rank=rank,
            )
        )
    return normalized
