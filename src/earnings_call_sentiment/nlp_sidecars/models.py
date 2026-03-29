"""Optional NLP sidecar model adapters and registry."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from earnings_call_sentiment import optional_runtime

from .base import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_MAX_LENGTH,
    BaseClassificationModel,
    BaseEmbeddingModel,
    ClassificationResult,
    EmbeddingResult,
    LabelScore,
    TextUnit,
    normalize_polarity_label,
    normalize_text_classification_scores,
    pipeline_device_index,
    resolve_runtime_device,
)


class FinBertToneModel(BaseClassificationModel):
    key = "finbert_tone"
    model_id = "yiyanghkust/finbert-tone"

    def __init__(self, *, device: str = "auto", cache_dir: str | None = None) -> None:
        super().__init__(device=device, cache_dir=cache_dir)
        self._classifier: Any | None = None

    def _load_classifier(self):
        if self._classifier is not None:
            return self._classifier
        transformers = optional_runtime.load_optional_dependency("transformers")
        kwargs: dict[str, Any] = {
            "task": "text-classification",
            "model": self.model_id,
            "device": pipeline_device_index(self.device),
        }
        if self.cache_dir:
            kwargs["model_kwargs"] = {"cache_dir": self.cache_dir}
        self._classifier = transformers.pipeline(**kwargs)
        return self._classifier

    def prewarm(self) -> dict[str, Any]:
        classifier = self._load_classifier()
        return {
            "model_name": self.key,
            "model_id": self.model_id,
            "output_kind": self.output_kind,
            "device": resolve_runtime_device(self.device),
            "task": getattr(classifier, "task", "text-classification"),
            "cache_dir": self.cache_dir,
        }

    def predict(
        self,
        units: list[TextUnit],
        *,
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_length: int = DEFAULT_MAX_LENGTH,
        label_groups: dict[str, list[str]] | None = None,
    ) -> list[ClassificationResult]:
        del label_groups
        if not units:
            return []
        classifier = self._load_classifier()
        raw_outputs = classifier(
            [unit.text for unit in units],
            batch_size=batch_size,
            truncation=True,
            max_length=max_length,
            top_k=None,
        )
        return [
            ClassificationResult(
                unit=unit,
                scores=scores,
                comparable_label=normalize_polarity_label(scores[0].label) if scores else None,
            )
            for unit, scores in (
                (
                    unit,
                    normalize_text_classification_scores(raw_output),
                )
                for unit, raw_output in zip(units, raw_outputs, strict=True)
            )
        ]


class FinancialRobertaModel(BaseClassificationModel):
    key = "financial_roberta"
    model_id = "soleimanian/financial-roberta-large-sentiment"

    def __init__(self, *, device: str = "auto", cache_dir: str | None = None) -> None:
        super().__init__(device=device, cache_dir=cache_dir)
        self._classifier: Any | None = None

    def _load_classifier(self):
        if self._classifier is not None:
            return self._classifier
        transformers = optional_runtime.load_optional_dependency("transformers")
        kwargs: dict[str, Any] = {
            "task": "text-classification",
            "model": self.model_id,
            "device": pipeline_device_index(self.device),
        }
        if self.cache_dir:
            kwargs["model_kwargs"] = {"cache_dir": self.cache_dir}
        self._classifier = transformers.pipeline(**kwargs)
        return self._classifier

    def _label_map(self) -> dict[str, str]:
        classifier = self._load_classifier()
        config = getattr(getattr(classifier, "model", None), "config", None)
        id2label = getattr(config, "id2label", {}) or {}
        mapped: dict[str, str] = {}
        for key, value in id2label.items():
            mapped[f"LABEL_{key}"] = str(value)
        return mapped

    def prewarm(self) -> dict[str, Any]:
        classifier = self._load_classifier()
        return {
            "model_name": self.key,
            "model_id": self.model_id,
            "output_kind": self.output_kind,
            "device": resolve_runtime_device(self.device),
            "task": getattr(classifier, "task", "text-classification"),
            "cache_dir": self.cache_dir,
        }

    def predict(
        self,
        units: list[TextUnit],
        *,
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_length: int = DEFAULT_MAX_LENGTH,
        label_groups: dict[str, list[str]] | None = None,
    ) -> list[ClassificationResult]:
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
            ClassificationResult(
                unit=unit,
                scores=scores,
                comparable_label=normalize_polarity_label(scores[0].label) if scores else None,
            )
            for unit, scores in (
                (
                    unit,
                    normalize_text_classification_scores(raw_output, label_map=label_map),
                )
                for unit, raw_output in zip(units, raw_outputs, strict=True)
            )
        ]


class DebertaZeroShotModel(BaseClassificationModel):
    key = "deberta_zero_shot"
    model_id = "MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli"

    def __init__(self, *, device: str = "auto", cache_dir: str | None = None) -> None:
        super().__init__(device=device, cache_dir=cache_dir)
        self._classifier: Any | None = None

    def _load_classifier(self):
        if self._classifier is not None:
            return self._classifier
        transformers = optional_runtime.load_optional_dependency("transformers")
        kwargs: dict[str, Any] = {
            "task": "zero-shot-classification",
            "model": self.model_id,
            "device": pipeline_device_index(self.device),
        }
        if self.cache_dir:
            kwargs["model_kwargs"] = {"cache_dir": self.cache_dir}
        self._classifier = transformers.pipeline(**kwargs)
        return self._classifier

    def prewarm(self) -> dict[str, Any]:
        classifier = self._load_classifier()
        return {
            "model_name": self.key,
            "model_id": self.model_id,
            "output_kind": self.output_kind,
            "device": resolve_runtime_device(self.device),
            "task": getattr(classifier, "task", "zero-shot-classification"),
            "cache_dir": self.cache_dir,
        }

    def predict(
        self,
        units: list[TextUnit],
        *,
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_length: int = DEFAULT_MAX_LENGTH,
        label_groups: dict[str, list[str]] | None = None,
    ) -> list[ClassificationResult]:
        if not units:
            return []
        if not label_groups:
            raise RuntimeError("DeBERTa zero-shot scoring requires a non-empty label-group config.")
        classifier = self._load_classifier()
        combined_rows: dict[str, dict[str, Any]] = {
            unit.unit_id: {"scores": [], "group_top_labels": {}} for unit in units
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
                rows = [
                    LabelScore(
                        label=str(label),
                        score=round(float(score), 6),
                        rank=rank,
                        metadata={"label_group": group_name},
                    )
                    for rank, (label, score) in enumerate(
                        zip(raw_output.get("labels", []), raw_output.get("scores", []), strict=False),
                        start=1,
                    )
                ]
                if rows:
                    combined_rows[unit.unit_id]["group_top_labels"][group_name] = {
                        "label": rows[0].label,
                        "score": rows[0].score,
                    }
                combined_rows[unit.unit_id]["scores"].extend(rows)

        results: list[ClassificationResult] = []
        for unit in units:
            score_rows = sorted(
                combined_rows[unit.unit_id]["scores"],
                key=lambda item: item.score,
                reverse=True,
            )
            reranked = [
                LabelScore(
                    label=item.label,
                    score=item.score,
                    rank=rank,
                    metadata=item.metadata,
                )
                for rank, item in enumerate(score_rows, start=1)
            ]
            tone_label = combined_rows[unit.unit_id]["group_top_labels"].get("tone", {}).get("label")
            results.append(
                ClassificationResult(
                    unit=unit,
                    scores=reranked,
                    comparable_label=normalize_polarity_label(str(tone_label)),
                    metadata={"group_top_labels": combined_rows[unit.unit_id]["group_top_labels"]},
                )
            )
        return results


class MpnetEmbeddingsModel(BaseEmbeddingModel):
    key = "mpnet_embeddings"
    model_id = "sentence-transformers/all-mpnet-base-v2"

    def __init__(self, *, device: str = "auto", cache_dir: str | None = None) -> None:
        super().__init__(device=device, cache_dir=cache_dir)
        self._tokenizer: Any | None = None
        self._model: Any | None = None

    def _load_runtime(self) -> tuple[Any, Any, Any]:
        if self._tokenizer is not None and self._model is not None:
            torch = optional_runtime.load_optional_dependency("torch")
            return torch, self._tokenizer, self._model
        transformers = optional_runtime.load_optional_dependency("transformers")
        torch = optional_runtime.load_optional_dependency("torch")
        kwargs: dict[str, Any] = {}
        if self.cache_dir:
            kwargs["cache_dir"] = self.cache_dir
        self._tokenizer = transformers.AutoTokenizer.from_pretrained(self.model_id, **kwargs)
        self._model = transformers.AutoModel.from_pretrained(self.model_id, **kwargs)
        self._model.to(resolve_runtime_device(self.device))
        self._model.eval()
        return torch, self._tokenizer, self._model

    def prewarm(self) -> dict[str, Any]:
        torch, _, model = self._load_runtime()
        hidden_size = int(getattr(getattr(model, "config", None), "hidden_size", 0) or 0)
        return {
            "model_name": self.key,
            "model_id": self.model_id,
            "output_kind": self.output_kind,
            "device": resolve_runtime_device(self.device),
            "embedding_dimension": hidden_size,
            "cache_dir": self.cache_dir,
            "torch_version": getattr(torch, "__version__", ""),
        }

    def _mean_pool(self, token_embeddings, attention_mask, torch_module):
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        sum_embeddings = (token_embeddings * input_mask_expanded).sum(1)
        sum_mask = input_mask_expanded.sum(1).clamp(min=1e-9)
        pooled = sum_embeddings / sum_mask
        return torch_module.nn.functional.normalize(pooled, p=2, dim=1)

    def embed(
        self,
        units: list[TextUnit],
        *,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> list[EmbeddingResult]:
        if not units:
            return []
        torch, tokenizer, model = self._load_runtime()
        resolved_device = resolve_runtime_device(self.device)
        outputs: list[EmbeddingResult] = []
        for start in range(0, len(units), batch_size):
            batch = units[start : start + batch_size]
            encoded = tokenizer(
                [unit.text for unit in batch],
                padding=True,
                truncation=True,
                max_length=DEFAULT_MAX_LENGTH,
                return_tensors="pt",
            )
            if resolved_device == "cuda":
                encoded = {key: value.to("cuda") for key, value in encoded.items()}
            with torch.no_grad():
                model_output = model(**encoded)
                embeddings = self._mean_pool(
                    model_output.last_hidden_state,
                    encoded["attention_mask"],
                    torch,
                )
            vectors = embeddings.detach().cpu().tolist()
            for unit, vector in zip(batch, vectors, strict=True):
                outputs.append(
                    EmbeddingResult(
                        unit=unit,
                        vector=[round(float(value), 8) for value in vector],
                        metadata={"similarity_only": True},
                    )
                )
        return outputs


MODEL_REGISTRY: dict[str, type[BaseClassificationModel | BaseEmbeddingModel]] = {
    FinBertToneModel.key: FinBertToneModel,
    FinancialRobertaModel.key: FinancialRobertaModel,
    DebertaZeroShotModel.key: DebertaZeroShotModel,
    MpnetEmbeddingsModel.key: MpnetEmbeddingsModel,
}

AVAILABLE_MODEL_NAMES = tuple(sorted(MODEL_REGISTRY))


def get_model_class(name: str):
    try:
        return MODEL_REGISTRY[name]
    except KeyError as exc:
        supported = ", ".join(AVAILABLE_MODEL_NAMES)
        raise RuntimeError(
            f"Unsupported NLP sidecar model '{name}'. Supported values: {supported}."
        ) from exc


def build_model(name: str, *, device: str = "auto", cache_dir: str | None = None):
    model_class = get_model_class(name)
    return model_class(device=device, cache_dir=cache_dir)


def model_metadata_from_results(results: list[ClassificationResult] | list[EmbeddingResult]) -> dict[str, Any]:
    if not results:
        return {}
    first = results[0]
    metadata: dict[str, Any] = {"unit_count": len(results)}
    if isinstance(first, ClassificationResult):
        metadata["sample_scores"] = [asdict(score) for score in first.scores[:3]]
    elif isinstance(first, EmbeddingResult):
        metadata["embedding_dimension"] = len(first.vector)
    return metadata
