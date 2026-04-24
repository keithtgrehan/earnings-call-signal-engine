"""Optional readiness helpers for future offline ASR and alignment workflows."""

from __future__ import annotations

from . import (
    AdapterDependency,
    dependency_hint as build_dependency_hint,
    missing_dependencies,
    require_dependencies,
)

OPTIONAL_GROUP = "audio"
DEPENDENCIES = (
    AdapterDependency("faster_whisper", "faster-whisper"),
    AdapterDependency("ffmpeg", "ffmpeg-python"),
)


def is_available() -> bool:
    return not missing_dependencies(DEPENDENCIES)


def dependency_hint() -> str:
    return build_dependency_hint(
        optional_groups=OPTIONAL_GROUP,
        dependencies=DEPENDENCIES,
        extra_note="WhisperX alignment remains optional roadmap work and may require manual installation.",
    )


def require_available() -> None:
    require_dependencies(
        adapter_name="signal_engine.adapters.asr",
        optional_groups=OPTIONAL_GROUP,
        dependencies=DEPENDENCIES,
        purpose="optional ASR and alignment preparation",
    )
