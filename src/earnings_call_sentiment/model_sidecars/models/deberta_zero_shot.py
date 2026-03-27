"""Zero-shot finance sidecars used for optional benchmark comparisons."""

from __future__ import annotations

from typing import Any

from earnings_call_sentiment import optional_runtime

from .base import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_MAX_LENGTH,
    BaseClassificationSidecar,
    ClassificationOutput,
    LabelScore,
    TextUnit,
    pipeline_device_index,
    resolve_runtime_device,
)


class BaseZeroShotSidecar(BaseClassificationSidecar):
    """Shared zero-shot implementation for heavier benchmark and lighter smoke models."""

    def __init__(self, *, device: str = "auto") -> None:
        super().__init__(device=device)
        self._classifier: Any | None = None

    def _load_classifier(self):
        if self._classifier is not None:
            return self._classifier

        transformers = optional_runtime.load_optional_dependency("transformers")
        self._classifier = transformers.pipeline(
            "zero-shot-classification",
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
            "task": getattr(classifier, "task", "zero-shot-classification"),
        }

    def predict(
        self,
        units: list[TextUnit],
        *,
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_length: int = DEFAULT_MAX_LENGTH,
        label_groups: dict[str, list[str]] | None = None,
    ) -> list[ClassificationOutput]:
        if not units:
            return []
        if not label_groups:
            raise RuntimeError(
                "Zero-shot scoring requires a non-empty zero-shot label config."
            )

        classifier = self._load_classifier()
        outputs_by_unit: dict[str, list[LabelScore]] = {
            unit.source_id: [] for unit in units
        }
        texts = [unit.text for unit in units]
        for group_name, labels in label_groups.items():
            raw_outputs = classifier(
                texts,
                candidate_labels=labels,
                multi_label=True,
                batch_size=batch_size,
                truncation=True,
                max_length=max_length,
            )
            if isinstance(raw_outputs, dict):
                raw_outputs = [raw_outputs]
            for unit, raw_output in zip(units, raw_outputs, strict=True):
                ranked_scores = [
                    LabelScore(
                        label=str(label),
                        score=round(float(score), 6),
                        rank=rank,
                        metadata={"label_group": group_name},
                    )
                    for rank, (label, score) in enumerate(
                        zip(
                            raw_output.get("labels", []),
                            raw_output.get("scores", []),
                            strict=False,
                        ),
                        start=1,
                    )
                ]
                outputs_by_unit[unit.source_id].extend(ranked_scores)

        return [
            ClassificationOutput(
                unit=unit,
                scores=outputs_by_unit[unit.source_id],
            )
            for unit in units
        ]


class DebertaZeroShotSidecar(BaseZeroShotSidecar):
    key = "deberta_zero_shot"
    model_id = "MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli"


class DistilbartZeroShotSmokeSidecar(BaseZeroShotSidecar):
    key = "distilbart_zero_shot_smoke"
    model_id = "valhalla/distilbart-mnli-12-1"
