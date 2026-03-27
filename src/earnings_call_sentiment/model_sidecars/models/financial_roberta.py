"""Financial RoBERTa sentiment sidecar."""

from __future__ import annotations

from typing import Any

from earnings_call_sentiment import optional_runtime

from .base import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_MAX_LENGTH,
    BaseClassificationSidecar,
    ClassificationOutput,
    TextUnit,
    normalize_text_classification_scores,
    pipeline_device_index,
    resolve_runtime_device,
)


class FinancialRobertaSidecar(BaseClassificationSidecar):
    key = "financial_roberta"
    model_id = "soleimanian/financial-roberta-large-sentiment"

    def __init__(self, *, device: str = "auto") -> None:
        super().__init__(device=device)
        self._classifier: Any | None = None

    def _label_map(self) -> dict[str, str]:
        classifier = self._load_classifier()
        config = getattr(getattr(classifier, "model", None), "config", None)
        id2label = getattr(config, "id2label", {}) or {}
        mapped: dict[str, str] = {}
        for key, value in id2label.items():
            mapped[f"LABEL_{key}"] = str(value)
        return mapped

    def _load_classifier(self):
        if self._classifier is not None:
            return self._classifier

        transformers = optional_runtime.load_optional_dependency("transformers")
        self._classifier = transformers.pipeline(
            "text-classification",
            model=self.model_id,
            device=pipeline_device_index(self.device),
        )
        return self._classifier

    def prewarm(self) -> dict[str, Any]:
        classifier = self._load_classifier()
        return {
            "model_name": self.key,
            "model_id": self.model_id,
            "output_kind": self.output_kind,
            "device": resolve_runtime_device(self.device),
            "task": getattr(classifier, "task", "text-classification"),
        }

    def predict(
        self,
        units: list[TextUnit],
        *,
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_length: int = DEFAULT_MAX_LENGTH,
        label_groups: dict[str, list[str]] | None = None,
    ) -> list[ClassificationOutput]:
        del label_groups
        if not units:
            return []

        classifier = self._load_classifier()
        label_map = self._label_map()
        raw_outputs = classifier(
            [unit.text for unit in units],
            batch_size=batch_size,
            truncation=True,
            max_length=max_length,
            top_k=None,
        )
        return [
            ClassificationOutput(
                unit=unit,
                scores=normalize_text_classification_scores(
                    raw_output,
                    label_map=label_map,
                ),
            )
            for unit, raw_output in zip(units, raw_outputs, strict=True)
        ]
