from __future__ import annotations

from pathlib import Path
from typing import Any

from data_layer.io import write_json, write_jsonl
from data_layer.schemas import SegmentRecord
from signal_engine.multimodal.video_features import extract_video_feature_set


def _is_flagged(segment: SegmentRecord, text_rows_by_id: dict[str, dict[str, Any]]) -> bool:
    text_row = text_rows_by_id.get(segment.segment_id, {})
    return (
        text_row.get("rule_signal") in {"risk_friction", "uncertainty_hedging"}
        or float(text_row.get("signal_uncertainty") or 0.0) >= 0.45
    )


def extract_video_features(
    segments: list[SegmentRecord],
    *,
    text_rows: list[dict[str, Any]],
    output_dir: Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    text_rows_by_id = {str(row["segment_id"]): row for row in text_rows}
    rows: list[dict[str, Any]] = []
    for segment in segments:
        flagged = _is_flagged(segment, text_rows_by_id)
        feature_set = extract_video_feature_set(segment.video_path) if flagged else None
        rows.append(
            {
                "segment_id": segment.segment_id,
                "flagged_for_video": flagged,
                "available": bool(feature_set.available) if feature_set else False,
                "video_path": segment.video_path,
                "visual_emotion": None,
                "engagement": None,
                "stress_indicator": None,
                "head_pose": None,
                "eye_movement": None,
                "motion_intensity": (feature_set.measurements.get("motion_proxy_mean") if feature_set else None),
                "measurements": dict(feature_set.measurements) if feature_set else {},
                "signals": [signal.to_dict() for signal in feature_set.signals] if feature_set else [],
                "limitations": (
                    feature_set.limitations
                    if feature_set
                    else ["Video was not run because the segment was not flagged or no video was provided."]
                ),
                "adapter_used": feature_set.adapter_used if feature_set else "event_trigger_gate",
            }
        )

    status = {
        "stage": "video",
        "status": "completed",
        "dry_run": dry_run,
        "segments": len(segments),
        "flagged_segments": sum(1 for row in rows if row["flagged_for_video"]),
        "available_rows": sum(1 for row in rows if row["available"]),
        "notes": ["Video runs only on flagged segments in v1."],
    }
    if not dry_run:
        write_jsonl(output_dir / "video_features.jsonl", rows)
        write_json(output_dir / "video_status.json", status)
    return {"rows": rows, "status": status}
