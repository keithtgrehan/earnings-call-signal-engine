"""Future adapter for optional offline audio-to-transcript workflows."""

from __future__ import annotations

from . import AdapterDependency, missing_dependencies, require_dependencies

OPTIONAL_GROUP = "audio"
DEPENDENCIES = (
    AdapterDependency("faster_whisper", "faster-whisper"),
    AdapterDependency("librosa", "librosa"),
    AdapterDependency("torchaudio", "torchaudio"),
    AdapterDependency("ffmpeg", "ffmpeg-python"),
)


def is_available() -> bool:
    return not missing_dependencies(DEPENDENCIES)


def require_available() -> None:
    require_dependencies(
        adapter_name="signal_engine.adapters.asr",
        optional_groups=OPTIONAL_GROUP,
        dependencies=DEPENDENCIES,
        purpose="optional ASR and alignment preparation",
    )
