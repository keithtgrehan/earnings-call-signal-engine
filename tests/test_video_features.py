from __future__ import annotations

from pathlib import Path

import pytest

from signal_engine.multimodal.video_features import extract_video_feature_set


def test_extract_video_feature_set_handles_missing_file() -> None:
    feature_set = extract_video_feature_set("/tmp/not-a-real-file.mp4")
    assert feature_set.available is False
    assert "does not exist" in " ".join(feature_set.limitations)


def test_extract_video_feature_set_from_tiny_video_if_opencv_available(tmp_path: Path) -> None:
    cv2 = pytest.importorskip("cv2")
    import numpy as np

    video_path = tmp_path / "tiny.avi"
    writer = cv2.VideoWriter(
        str(video_path),
        cv2.VideoWriter_fourcc(*"MJPG"),
        5.0,
        (32, 32),
    )
    if not writer.isOpened():
        pytest.skip("OpenCV video writer is unavailable in this environment.")

    for value in (10, 40, 90):
        frame = np.full((32, 32, 3), value, dtype=np.uint8)
        writer.write(frame)
    writer.release()

    feature_set = extract_video_feature_set(video_path)
    assert feature_set.available is True
    assert feature_set.measurements["frame_count"] >= 1
