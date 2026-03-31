from __future__ import annotations

import pytest

from earnings_call_sentiment.model_sidecars.models.registry import (
    AVAILABLE_MODEL_NAMES,
    build_model,
    get_model_class,
)


def test_model_registry_lists_expected_models() -> None:
    assert AVAILABLE_MODEL_NAMES == (
        "deberta_zero_shot",
        "distilbart_zero_shot_smoke",
        "financial_roberta",
        "finbert_tone",
        "mpnet_embeddings",
    )


def test_build_model_returns_requested_sidecar() -> None:
    model = build_model("finbert_tone", device="cpu")
    assert model.key == "finbert_tone"
    assert model.model_id == "yiyanghkust/finbert-tone"


def test_get_model_class_rejects_unknown_model() -> None:
    with pytest.raises(RuntimeError, match="Unsupported model-sidecar"):
        get_model_class("unknown_model")
