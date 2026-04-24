"""Future adapter for optional transcript emotion inference benchmarks."""

from __future__ import annotations

from . import AdapterDependency, missing_dependencies, require_dependencies

OPTIONAL_GROUP = "text-emotion"
DEPENDENCIES = (
    AdapterDependency("transformers", "transformers"),
    AdapterDependency("torch", "torch"),
    AdapterDependency("datasets", "datasets"),
    AdapterDependency("evaluate", "evaluate"),
)


def is_available() -> bool:
    return not missing_dependencies(DEPENDENCIES)


def require_available() -> None:
    require_dependencies(
        adapter_name="signal_engine.adapters.text_emotion",
        optional_group=OPTIONAL_GROUP,
        dependencies=DEPENDENCIES,
        purpose="text emotion benchmarking and optional enrichment",
    )
