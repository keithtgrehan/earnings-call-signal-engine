"""Future adapter for optional embedding and retrieval-side benchmarks."""

from __future__ import annotations

from . import AdapterDependency, missing_dependencies, require_dependencies

OPTIONAL_GROUP = "embeddings"
DEPENDENCIES = (
    AdapterDependency("sentence_transformers", "sentence-transformers"),
    AdapterDependency("faiss", "faiss-cpu"),
    AdapterDependency("chromadb", "chromadb"),
)


def is_available() -> bool:
    return not missing_dependencies(DEPENDENCIES)


def require_available() -> None:
    require_dependencies(
        adapter_name="signal_engine.adapters.retrieval",
        optional_group=OPTIONAL_GROUP,
        dependencies=DEPENDENCIES,
        purpose="embedding, semantic lookup, and benchmark retrieval experiments",
    )
