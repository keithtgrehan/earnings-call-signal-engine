"""Future adapter for optional speaker diarization on raw audio inputs."""

from __future__ import annotations

from . import AdapterDependency, missing_dependencies, require_dependencies

OPTIONAL_GROUP = "diarization"
DEPENDENCIES = (
    AdapterDependency("pyannote.audio", "pyannote.audio"),
)


def is_available() -> bool:
    return not missing_dependencies(DEPENDENCIES)


def require_available() -> None:
    require_dependencies(
        adapter_name="signal_engine.adapters.diarization",
        optional_group=OPTIONAL_GROUP,
        dependencies=DEPENDENCIES,
        purpose="speaker diarization experiments",
    )
