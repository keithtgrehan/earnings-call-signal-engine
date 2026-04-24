"""Optional benchmark-only transformer emotion adapter.

This adapter is intentionally lazy. It reports capability and can build a local
pipeline only when the dependency stack and model cache are already present.
It does not make transformer emotion inference canonical.
"""

from __future__ import annotations

from . import (
    AdapterDependency,
    dependency_hint as build_dependency_hint,
    missing_dependencies,
    require_dependencies,
)

OPTIONAL_GROUP = "text-emotion"
DEPENDENCIES = (
    AdapterDependency("transformers", "transformers"),
    AdapterDependency("torch", "torch"),
)


def is_available() -> bool:
    return not missing_dependencies(DEPENDENCIES)


def dependency_hint() -> str:
    return build_dependency_hint(
        optional_groups=OPTIONAL_GROUP,
        dependencies=DEPENDENCIES,
        extra_note="This path is benchmark-only and must not replace deterministic transcript scoring.",
    )


def require_available() -> None:
    require_dependencies(
        adapter_name="signal_engine.adapters.optional_transformer_emotion",
        optional_groups=OPTIONAL_GROUP,
        dependencies=DEPENDENCIES,
        purpose="optional transformer emotion benchmarking",
    )


def load_local_text_classifier(model_id: str):
    require_available()
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

    tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(model_id, local_files_only=True)
    return pipeline("text-classification", model=model, tokenizer=tokenizer, top_k=None)


__all__ = ["dependency_hint", "is_available", "load_local_text_classifier", "require_available"]
