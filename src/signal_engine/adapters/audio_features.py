"""Future adapter for optional acoustic and prosody feature extraction."""

from __future__ import annotations

from . import AdapterDependency, missing_dependencies, require_dependencies

OPTIONAL_GROUP = "audio,prosody"
DEPENDENCIES = (
    AdapterDependency("librosa", "librosa"),
    AdapterDependency("torchaudio", "torchaudio"),
    AdapterDependency("opensmile", "opensmile"),
)


def is_available() -> bool:
    return not missing_dependencies(DEPENDENCIES)


def require_available() -> None:
    require_dependencies(
        adapter_name="signal_engine.adapters.audio_features",
        optional_groups=OPTIONAL_GROUP,
        dependencies=DEPENDENCIES,
        purpose="audio feature benchmarks and prosody review",
    )
