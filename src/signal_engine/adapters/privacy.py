"""Optional readiness helpers for Presidio-backed privacy enhancement.

Signal Engine ships with a deterministic fallback redaction layer in
`signal_engine.privacy`. This adapter only reports whether optional Presidio
enhancements are available locally.
"""

from __future__ import annotations

from . import (
    AdapterDependency,
    dependency_hint as build_dependency_hint,
    missing_dependencies,
    require_dependencies,
)

OPTIONAL_GROUP = "privacy"
DEPENDENCIES = (
    AdapterDependency("presidio_analyzer", "presidio-analyzer"),
    AdapterDependency("presidio_anonymizer", "presidio-anonymizer"),
)


def is_available() -> bool:
    return not missing_dependencies(DEPENDENCIES)


def dependency_hint() -> str:
    return build_dependency_hint(
        optional_groups=OPTIONAL_GROUP,
        dependencies=DEPENDENCIES,
        extra_note="The deterministic fallback in `signal_engine.privacy` works without Presidio.",
    )


def require_available() -> None:
    require_dependencies(
        adapter_name="signal_engine.adapters.privacy",
        optional_groups=OPTIONAL_GROUP,
        dependencies=DEPENDENCIES,
        purpose="privacy-safe transcript redaction and review preparation",
    )
