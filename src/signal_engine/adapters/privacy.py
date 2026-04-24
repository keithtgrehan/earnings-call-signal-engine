"""Future adapter for optional PII detection and transcript anonymization."""

from __future__ import annotations

from . import AdapterDependency, missing_dependencies, require_dependencies

OPTIONAL_GROUP = "privacy"
DEPENDENCIES = (
    AdapterDependency("presidio_analyzer", "presidio-analyzer"),
    AdapterDependency("presidio_anonymizer", "presidio-anonymizer"),
)


def is_available() -> bool:
    return not missing_dependencies(DEPENDENCIES)


def require_available() -> None:
    require_dependencies(
        adapter_name="signal_engine.adapters.privacy",
        optional_groups=OPTIONAL_GROUP,
        dependencies=DEPENDENCIES,
        purpose="privacy-safe transcript redaction and review preparation",
    )
