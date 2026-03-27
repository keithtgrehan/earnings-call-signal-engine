"""Registry for optional benchmark model sidecars."""

from __future__ import annotations

from .base import BaseModelSidecar
from .deberta_zero_shot import (
    DebertaZeroShotSidecar,
    DistilbartZeroShotSmokeSidecar,
)
from .financial_roberta import FinancialRobertaSidecar
from .finbert_tone import FinBertToneSidecar
from .mpnet_embeddings import MpnetEmbeddingsSidecar

MODEL_REGISTRY: dict[str, type[BaseModelSidecar]] = {
    FinBertToneSidecar.key: FinBertToneSidecar,
    FinancialRobertaSidecar.key: FinancialRobertaSidecar,
    DebertaZeroShotSidecar.key: DebertaZeroShotSidecar,
    DistilbartZeroShotSmokeSidecar.key: DistilbartZeroShotSmokeSidecar,
    MpnetEmbeddingsSidecar.key: MpnetEmbeddingsSidecar,
}

AVAILABLE_MODEL_NAMES = tuple(sorted(MODEL_REGISTRY))


def get_model_class(name: str) -> type[BaseModelSidecar]:
    try:
        return MODEL_REGISTRY[name]
    except KeyError as exc:
        supported = ", ".join(AVAILABLE_MODEL_NAMES)
        raise RuntimeError(
            f"Unsupported model-sidecar '{name}'. Supported values: {supported}."
        ) from exc


def build_model(name: str, *, device: str = "auto") -> BaseModelSidecar:
    model_class = get_model_class(name)
    return model_class(device=device)
