"""Sentence-transformer MPNet embeddings sidecar."""

from __future__ import annotations

from typing import Any

from earnings_call_sentiment import optional_runtime

from .base import (
    DEFAULT_BATCH_SIZE,
    BaseEmbeddingSidecar,
    EmbeddingOutput,
    TextUnit,
    resolve_runtime_device,
)


class MpnetEmbeddingsSidecar(BaseEmbeddingSidecar):
    key = "mpnet_embeddings"
    model_id = "sentence-transformers/all-mpnet-base-v2"

    def __init__(self, *, device: str = "auto") -> None:
        super().__init__(device=device)
        self._model: Any | None = None

    def _load_model(self):
        if self._model is not None:
            return self._model

        sentence_transformers = optional_runtime.load_optional_dependency(
            "sentence_transformers",
            package_name="sentence-transformers",
        )
        self._model = sentence_transformers.SentenceTransformer(
            self.model_id,
            device=resolve_runtime_device(self.device),
        )
        return self._model

    def prewarm(self) -> dict[str, Any]:
        model = self._load_model()
        embedding_dimension = 0
        if hasattr(model, "get_sentence_embedding_dimension"):
            embedding_dimension = int(model.get_sentence_embedding_dimension() or 0)
        return {
            "model_name": self.key,
            "model_id": self.model_id,
            "output_kind": self.output_kind,
            "device": resolve_runtime_device(self.device),
            "embedding_dimension": embedding_dimension,
        }

    def encode_texts(
        self,
        texts: list[str],
        *,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> list[list[float]]:
        if not texts:
            return []
        model = self._load_model()
        vectors = model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [[float(value) for value in row] for row in vectors.tolist()]

    def embed(
        self,
        units: list[TextUnit],
        *,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> list[EmbeddingOutput]:
        vectors = self.encode_texts(
            [unit.text for unit in units],
            batch_size=batch_size,
        )
        return [
            EmbeddingOutput(unit=unit, vector=vector)
            for unit, vector in zip(units, vectors, strict=True)
        ]
