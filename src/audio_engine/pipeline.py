from __future__ import annotations

from pathlib import Path
from typing import Any

from data_layer.io import write_json, write_jsonl
from data_layer.schemas import SegmentRecord
from signal_engine.multimodal.audio_features import extract_audio_feature_set


def _bounded(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 4)


def _audio_row(segment: SegmentRecord) -> dict[str, Any]:
    feature_set = extract_audio_feature_set(segment.audio_path)
    measurements = dict(feature_set.measurements)
    silence_ratio = float(measurements.get("silence_ratio") or 0.0)
    activity_ratio = float(measurements.get("activity_ratio") or 0.0)
    rms_std = float(measurements.get("rms_std") or 0.0)
    duration = float(measurements.get("duration_seconds") or 0.0)
    word_count = len(segment.text.split())
    speech_rate = (word_count / duration) * 60.0 if duration > 0 else 0.0
    return {
        "segment_id": segment.segment_id,
        "available": feature_set.available,
        "audio_path": segment.audio_path,
        "pause_duration": round(silence_ratio * duration, 4) if duration else None,
        "speech_rate": round(speech_rate, 4),
        "pitch": None,
        "energy": measurements.get("rms_mean"),
        "jitter": None,
        "shimmer": None,
        "hesitation_score": _bounded(silence_ratio + (0.15 if speech_rate and speech_rate < 95 else 0.0)),
        "confidence_score": _bounded(activity_ratio - min(rms_std, 0.35)),
        "intensity_score": _bounded(float(measurements.get("rms_mean") or 0.0) + rms_std),
        "measurements": measurements,
        "signals": [signal.to_dict() for signal in feature_set.signals],
        "limitations": feature_set.limitations,
        "adapter_used": feature_set.adapter_used,
    }


def extract_audio_features(
    segments: list[SegmentRecord],
    *,
    output_dir: Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    rows = [_audio_row(segment) for segment in segments]
    status = {
        "stage": "audio",
        "status": "completed",
        "dry_run": dry_run,
        "segments": len(segments),
        "available_rows": sum(1 for row in rows if row["available"]),
        "notes": ["Audio cues are augmentation only and never override transcript evidence."],
    }
    if not dry_run:
        write_jsonl(output_dir / "audio_features.jsonl", rows)
        write_json(output_dir / "audio_status.json", status)
    return {"rows": rows, "status": status}
