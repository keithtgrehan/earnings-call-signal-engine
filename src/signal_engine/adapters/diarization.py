"""Optional readiness helpers for future speaker diarization experiments."""

from __future__ import annotations

from . import (
    AdapterDependency,
    dependency_hint as build_dependency_hint,
    missing_dependencies,
    require_dependencies,
)

OPTIONAL_GROUP = "diarization"
DEPENDENCIES = (
    AdapterDependency("pyannote.audio", "pyannote.audio"),
)


def is_available() -> bool:
    return not missing_dependencies(DEPENDENCIES)


def dependency_hint() -> str:
    return build_dependency_hint(
        optional_groups=OPTIONAL_GROUP,
        dependencies=DEPENDENCIES,
        extra_note="Some pyannote assets are token-gated and are intentionally not required by default.",
    )


def require_available() -> None:
    require_dependencies(
        adapter_name="signal_engine.adapters.diarization",
        optional_groups=OPTIONAL_GROUP,
        dependencies=DEPENDENCIES,
        purpose="speaker diarization experiments",
    )
