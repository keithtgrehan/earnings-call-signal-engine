from __future__ import annotations

from earnings_call_sentiment.media_support_eval import build_visual_trainability_report, validate_media_support_eval
from earnings_call_sentiment.visual import runtime as visual_runtime


def test_media_support_eval_seed_set_validates() -> None:
    summary = validate_media_support_eval()
    assert summary["status"] == "ok"
    assert summary["manifest_rows"] >= 2
    assert summary["label_rows"] >= 20
    assert summary["label_counts_by_modality"]["audio"] >= 10
    assert summary["runtime_smoke_rows"] >= 3


def test_visual_trainability_report_honestly_flags_single_group_gap() -> None:
    report = build_visual_trainability_report()

    assert report["video_label_rows_total"] >= 12
    assert report["video_label_rows_with_visual_tension"] >= 6
    assert report["source_groups_with_visual_tension_labels"] == 1
    assert report["basic_grouped_eval_ready"] is False
    assert report["defensible_grouped_eval_ready"] is False
    assert report["calibration_ready"] is False
    assert report["minimum_next_data"]["additional_groups_for_basic_grouped_eval"] == 1
    assert report["minimum_next_data"]["additional_groups_for_defensible_grouped_eval"] == 2


def test_multimodal_runtime_status_reports_expected_keys(monkeypatch) -> None:
    class DummyCV2:
        __version__ = "4.10.0"

    class DummyMP:
        __version__ = "0.10.32"
        solutions = object()

    class DummyVision:
        FaceLandmarker = object
        PoseLandmarker = object

    monkeypatch.setattr(visual_runtime, "load_cv2", lambda: DummyCV2())
    monkeypatch.setattr(visual_runtime, "load_mediapipe", lambda: DummyMP())
    monkeypatch.setattr(visual_runtime, "mediapipe_tasks_vision", lambda: DummyVision())

    status = visual_runtime.multimodal_runtime_status()
    assert status["cv2_import_ok"] is True
    assert status["mediapipe_import_ok"] is True
    assert status["face_landmarker_available"] is True
    assert status["pose_landmarker_available"] is True
