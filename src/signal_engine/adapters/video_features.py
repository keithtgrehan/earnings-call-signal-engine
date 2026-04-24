"""Future adapter for optional escalation-only video feature extraction."""

from __future__ import annotations

from . import AdapterDependency, missing_dependencies, require_dependencies

OPTIONAL_GROUP = "video"
DEPENDENCIES = (
    AdapterDependency("cv2", "opencv-python"),
    AdapterDependency("scenedetect", "scenedetect"),
    AdapterDependency("moviepy", "moviepy"),
)


def is_available() -> bool:
    return not missing_dependencies(DEPENDENCIES)


def require_available() -> None:
    require_dependencies(
        adapter_name="signal_engine.adapters.video_features",
        optional_groups=OPTIONAL_GROUP,
        dependencies=DEPENDENCIES,
        purpose="video keyframe and scene review on escalated cases only",
    )
