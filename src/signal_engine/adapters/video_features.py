"""Optional readiness helpers for escalation-only video preprocessing."""

from __future__ import annotations

from . import (
    AdapterDependency,
    dependency_hint as build_dependency_hint,
    missing_dependencies,
    require_dependencies,
)

OPTIONAL_GROUP = "video"
DEPENDENCIES = (
    AdapterDependency("cv2", "opencv-python"),
    AdapterDependency("scenedetect", "scenedetect"),
)


def is_available() -> bool:
    return not missing_dependencies(DEPENDENCIES)


def dependency_hint() -> str:
    return build_dependency_hint(
        optional_groups=OPTIONAL_GROUP,
        dependencies=DEPENDENCIES,
        extra_note="MoviePy remains optional later if clip assembly is needed.",
    )


def require_available() -> None:
    require_dependencies(
        adapter_name="signal_engine.adapters.video_features",
        optional_groups=OPTIONAL_GROUP,
        dependencies=DEPENDENCIES,
        purpose="video keyframe and scene review on escalated cases only",
    )
