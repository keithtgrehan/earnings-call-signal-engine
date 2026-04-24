"""Optional readiness helpers for benchmark-only retrieval experiments."""

from __future__ import annotations

from . import (
    AdapterDependency,
    dependency_hint as build_dependency_hint,
    missing_dependencies,
    require_dependencies,
)

OPTIONAL_GROUP = "embeddings"
DEPENDENCIES = (
    AdapterDependency("sentence_transformers", "sentence-transformers"),
    AdapterDependency("faiss", "faiss-cpu"),
    AdapterDependency("chromadb", "chromadb"),
)


def is_available() -> bool:
    return not missing_dependencies(DEPENDENCIES)


def dependency_hint() -> str:
    return build_dependency_hint(
        optional_groups=OPTIONAL_GROUP,
        dependencies=DEPENDENCIES,
        extra_note="Retrieval remains optional enrichment and never replaces transcript evidence.",
    )


def require_available() -> None:
    require_dependencies(
        adapter_name="signal_engine.adapters.retrieval",
        optional_groups=OPTIONAL_GROUP,
        dependencies=DEPENDENCIES,
        purpose="embedding, semantic lookup, and benchmark retrieval experiments",
    )
