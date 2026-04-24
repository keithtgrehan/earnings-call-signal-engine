"""Optional readiness helpers for future acoustic and prosody feature work."""

from __future__ import annotations

from . import (
    AdapterDependency,
    dependency_hint as build_dependency_hint,
    missing_dependencies,
    require_dependencies,
)

OPTIONAL_GROUP = "audio,prosody"
DEPENDENCIES = (
    AdapterDependency("librosa", "librosa"),
    AdapterDependency("torchaudio", "torchaudio"),
    AdapterDependency("opensmile", "opensmile"),
)


def is_available() -> bool:
    return not missing_dependencies(DEPENDENCIES)


def dependency_hint() -> str:
    return build_dependency_hint(
        optional_groups=OPTIONAL_GROUP,
        dependencies=DEPENDENCIES,
        extra_note="These features stay benchmark-only and do not change canonical scoring.",
    )


def require_available() -> None:
    require_dependencies(
        adapter_name="signal_engine.adapters.audio_features",
        optional_groups=OPTIONAL_GROUP,
        dependencies=DEPENDENCIES,
        purpose="audio feature benchmarks and prosody review",
    )
