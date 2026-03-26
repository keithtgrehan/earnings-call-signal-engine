from __future__ import annotations

import pytest

from earnings_call_sentiment import optional_runtime
from earnings_call_sentiment.model_sidecars.models.finbert_tone import FinBertToneSidecar
from earnings_call_sentiment.model_sidecars.models.mpnet_embeddings import (
    MpnetEmbeddingsSidecar,
)
from earnings_call_sentiment.model_sidecars.models.base import TextUnit


def test_classifier_fails_cleanly_when_transformers_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    def _missing_dependency(module_name: str, *, package_name: str | None = None):
        del package_name
        if module_name == "transformers":
            raise RuntimeError("Optional dependency 'transformers' is not available.")
        return optional_runtime.load_optional_dependency(module_name)

    monkeypatch.setattr(optional_runtime, "load_optional_dependency", _missing_dependency)
    model = FinBertToneSidecar(device="cpu")

    with pytest.raises(RuntimeError, match="transformers"):
        model.predict(
            [
                TextUnit(
                    case_id="case",
                    unit_type="chunks",
                    source_id="row-1",
                    text="Prepared remarks.",
                )
            ]
        )


def test_embedding_model_fails_cleanly_when_sentence_transformers_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _missing_dependency(module_name: str, *, package_name: str | None = None):
        del package_name
        if module_name == "sentence_transformers":
            raise RuntimeError(
                "Optional dependency 'sentence_transformers' is not available."
            )
        return optional_runtime.load_optional_dependency(module_name)

    monkeypatch.setattr(optional_runtime, "load_optional_dependency", _missing_dependency)
    model = MpnetEmbeddingsSidecar(device="cpu")

    with pytest.raises(RuntimeError, match="sentence_transformers"):
        model.embed(
            [
                TextUnit(
                    case_id="case",
                    unit_type="chunks",
                    source_id="row-1",
                    text="Prepared remarks.",
                )
            ]
        )
