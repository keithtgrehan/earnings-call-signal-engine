from __future__ import annotations

from pathlib import Path

import numpy as np

from .schemas import EvidenceWindow, ModalityFeatureSet, SignalFeature


def _unsupported(path: str | None, reason: str) -> ModalityFeatureSet:
    return ModalityFeatureSet(
        modality="video",
        available=False,
        source_path=path,
        limitations=[reason, "Video cues remain optional review support only."],
        adapter_used="opencv_video_proxy",
    )


def extract_video_feature_set(path: str | Path | None) -> ModalityFeatureSet:
    if path is None:
        return _unsupported(None, "No video file was provided.")

    file_path = Path(path)
    if not file_path.exists():
        return _unsupported(str(file_path), "Video file does not exist.")

    try:
        import cv2
    except ImportError:
        return _unsupported(str(file_path), "OpenCV is not installed. Install the optional video extra for frame analysis.")

    capture = cv2.VideoCapture(str(file_path))
    if not capture.isOpened():
        return _unsupported(str(file_path), "Video file could not be opened by OpenCV.")

    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    brightness_values: list[float] = []
    motion_values: list[float] = []
    previous_gray = None

    while True:
        ok, frame = capture.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness_values.append(float(np.mean(gray)))
        if previous_gray is not None:
            motion_values.append(float(np.mean(cv2.absdiff(gray, previous_gray))))
        previous_gray = gray
    capture.release()

    if not brightness_values:
        return _unsupported(str(file_path), "Video file contained no readable frames.")

    duration_seconds = (frame_count / fps) if fps > 0 else None
    brightness_mean = float(np.mean(brightness_values))
    brightness_std = float(np.std(brightness_values))
    motion_mean = float(np.mean(motion_values)) if motion_values else 0.0

    try:
        import mediapipe  # noqa: F401

        mediapipe_available = True
    except ImportError:
        mediapipe_available = False

    signals: list[SignalFeature] = []
    if motion_mean > 2.0:
        signals.append(
            SignalFeature(
                signal_name="motion_change_proxy",
                modality="video",
                strength="high" if motion_mean > 8.0 else "medium",
                confidence=min(0.66, 0.36 + (motion_mean / 20.0)),
                reason="Frame-difference motion proxy suggests visible movement changes worth review.",
                recommended_review_action="Review the clip manually before inferring gesture or posture meaning.",
                evidence_window=EvidenceWindow(
                    start_seconds=0.0 if duration_seconds is not None else None,
                    end_seconds=round(duration_seconds, 3) if duration_seconds is not None else None,
                    description="Whole video file",
                ),
                measurements={"motion_proxy_mean": round(motion_mean, 4)},
            )
        )

    limitations = [
        "Current video support is limited to quality and motion proxies.",
        "Face, gaze, gesture, and posture interpretation remain optional future work.",
    ]
    if mediapipe_available:
        limitations.append("MediaPipe appears available locally, but landmark inference is intentionally not canonical here.")

    return ModalityFeatureSet(
        modality="video",
        available=True,
        source_path=str(file_path),
        measurements={
            "frame_count": frame_count,
            "fps": round(fps, 4),
            "duration_seconds": round(duration_seconds, 4) if duration_seconds is not None else None,
            "brightness_mean": round(brightness_mean, 4),
            "brightness_std": round(brightness_std, 4),
            "motion_proxy_mean": round(motion_mean, 4),
            "mediapipe_available": mediapipe_available,
        },
        signals=signals,
        limitations=limitations,
        adapter_used="opencv_video_proxy",
    )


__all__ = ["extract_video_feature_set"]
