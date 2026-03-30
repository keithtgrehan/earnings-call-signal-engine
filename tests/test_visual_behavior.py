from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from earnings_call_sentiment import cli
from earnings_call_sentiment.visual.segment_aggregate import aggregate_visual_segments
from earnings_call_sentiment.visual.frame_extract import VideoMetadata
from earnings_call_sentiment.visual.summary import (
    compute_visual_behavior_outputs,
    summarize_visual_behavior_frames,
)


def test_visual_behavior_summary_handles_missing_video() -> None:
    payload = compute_visual_behavior_outputs(None, pd.DataFrame())
    assert payload["frames_df"].empty
    assert payload["segments_df"].empty
    assert payload["summary"]["video_available"] is False
    assert payload["summary"]["visual_features_available"] is False


def test_visual_segment_aggregation_builds_labels_and_notes() -> None:
    frames_df = pd.DataFrame(
        [
            {
                "timestamp_s": 0.0,
                "frame_index": 0,
                "face_visible": True,
                "landmark_confidence": 0.9,
                "face_size_ratio": 0.12,
                "motion_score": 0.02,
                "head_shift_score": 0.01,
                "head_yaw": 0.02,
                "head_pitch": 0.01,
                "head_roll": 0.01,
                "gaze_shift_proxy": 0.01,
                "blink_proxy": 0.0,
                "mouth_open_ratio": 0.03,
                "lower_face_tension_proxy": 0.02,
                "pose_visible": True,
                "shoulder_shift_score": 0.01,
            },
            {
                "timestamp_s": 1.0,
                "frame_index": 30,
                "face_visible": True,
                "landmark_confidence": 0.92,
                "face_size_ratio": 0.13,
                "motion_score": 0.2,
                "head_shift_score": 0.18,
                "head_yaw": 0.2,
                "head_pitch": 0.1,
                "head_roll": 0.08,
                "gaze_shift_proxy": 0.14,
                "blink_proxy": 1.0,
                "mouth_open_ratio": 0.08,
                "lower_face_tension_proxy": 0.15,
                "pose_visible": True,
                "shoulder_shift_score": 0.15,
            },
            {
                "timestamp_s": 2.0,
                "frame_index": 60,
                "face_visible": False,
                "landmark_confidence": 0.0,
                "face_size_ratio": 0.0,
                "motion_score": 0.0,
                "head_shift_score": 0.0,
                "head_yaw": 0.0,
                "head_pitch": 0.0,
                "head_roll": 0.0,
                "gaze_shift_proxy": 0.0,
                "blink_proxy": 0.0,
                "mouth_open_ratio": 0.0,
                "lower_face_tension_proxy": 0.0,
                "pose_visible": False,
                "shoulder_shift_score": 0.0,
            },
        ]
    )
    qa_segments_df = pd.DataFrame(
        [
            {"segment_id": 0, "start": 0.0, "end": 0.9, "phase": "prepared_remarks", "speaker_role": "management", "text": "Prepared."},
            {"segment_id": 1, "start": 1.0, "end": 2.1, "phase": "q_and_a", "speaker_role": "management", "text": "Answer."},
        ]
    )
    segments_df = aggregate_visual_segments(frames_df, qa_segments_df)
    assert list(segments_df["visual_stability_label"]) == ["stable", "somewhat_changed"]
    assert segments_df.iloc[0]["confidence_note"] == "usable visual segment"
    assert segments_df.iloc[1]["confidence_note"] == "usable visual segment"


def test_visual_summary_quality_gate_suppresses_weak_face_visibility() -> None:
    frames_df = pd.DataFrame(
        [
            {
                "timestamp_s": 0.0,
                "frame_index": 0,
                "face_detected": False,
                "face_count": 0,
                "face_visible": False,
                "landmark_confidence": 0.1,
                "face_size_ratio": 0.01,
                "motion_score": 0.01,
                "head_shift_score": 0.0,
                "head_yaw": 0.0,
                "head_pitch": 0.0,
                "head_roll": 0.0,
                "gaze_shift_proxy": 0.0,
                "blink_proxy": 0.0,
                "mouth_open_ratio": 0.0,
                "lower_face_tension_proxy": 0.0,
                "pose_visible": False,
                "hand_visible": False,
                "shoulder_shift_score": 0.0,
                "feature_note": "no_face_detected",
            },
            {
                "timestamp_s": 1.0,
                "frame_index": 30,
                "face_detected": True,
                "face_count": 1,
                "face_visible": False,
                "landmark_confidence": 0.2,
                "face_size_ratio": 0.02,
                "motion_score": 0.03,
                "head_shift_score": 0.0,
                "head_yaw": 0.0,
                "head_pitch": 0.0,
                "head_roll": 0.0,
                "gaze_shift_proxy": 0.0,
                "blink_proxy": 0.0,
                "mouth_open_ratio": 0.0,
                "lower_face_tension_proxy": 0.0,
                "pose_visible": False,
                "hand_visible": False,
                "shoulder_shift_score": 0.0,
                "feature_note": "low_face_visibility",
            },
        ]
    )
    qa_segments_df = pd.DataFrame(
        [
            {"segment_id": 0, "start": 0.0, "end": 1.2, "phase": "q_and_a", "speaker_role": "management", "text": "Answer."},
        ]
    )
    payload = summarize_visual_behavior_frames(
        frames_df,
        qa_segments_df,
        VideoMetadata(
            path=Path("/tmp/demo.mp4"),
            duration_s=2.0,
            fps=30.0,
            frame_count=60,
            width=640,
            height=360,
        ),
        sample_fps=1.0,
    )

    assert payload["summary"]["video_quality_ok"] is False
    assert payload["summary"]["visual_confidence_support"]["suppressed"] is True
    assert payload["summary"]["quality_gate"]["stable_face_frame_pct_ok"] is False
    assert payload["summary"]["visual_confidence_support"]["reason"] == "quality gate suppressed visual usability"
    assert "reviewer context only" in " ".join(payload["summary"]["notes"])
