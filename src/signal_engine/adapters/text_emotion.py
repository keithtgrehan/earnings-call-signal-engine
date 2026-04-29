"""Optional readiness helpers for local text-emotion benchmark backends.

This adapter never loads models at import time. It only reports whether the
core transformer runtime is present and how to enable it.
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
        extra_note="For expanded benchmark workflows, `datasets` and `evaluate` can be added separately.",
    )


def require_available() -> None:
    require_dependencies(
        adapter_name="signal_engine.adapters.text_emotion",
        optional_groups=OPTIONAL_GROUP,
        dependencies=DEPENDENCIES,
        purpose="text emotion benchmarking and optional enrichment",
    )
