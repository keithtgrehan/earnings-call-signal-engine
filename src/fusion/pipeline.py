from __future__ import annotations

from pathlib import Path
from typing import Any

from data_layer.io import write_json, write_jsonl
from signal_engine.signal_baseline import SIGNAL_FAMILY_LABELS


def _audio_adjustment(row: dict[str, Any] | None) -> dict[str, float]:
    if not row or not row.get("available"):
        return {label: 0.0 for label in SIGNAL_FAMILY_LABELS}
    hesitation = float(row.get("hesitation_score") or 0.0)
    confidence = float(row.get("confidence_score") or 0.0)
    intensity = float(row.get("intensity_score") or 0.0)
    return {
        "risk_friction": min(0.12, intensity * 0.08),
        "opportunity_commitment": min(0.10, confidence * 0.08),
        "uncertainty_hedging": min(0.14, hesitation * 0.10),
        "neutral": 0.0,
    }


def _video_adjustment(row: dict[str, Any] | None) -> dict[str, float]:
    if not row or not row.get("available"):
        return {label: 0.0 for label in SIGNAL_FAMILY_LABELS}
    motion = float(row.get("motion_intensity") or 0.0)
    stress = float(row.get("stress_indicator") or 0.0)
    return {
        "risk_friction": min(0.10, (motion / 100.0) + (stress * 0.05)),
        "opportunity_commitment": 0.0,
        "uncertainty_hedging": min(0.08, stress * 0.08),
        "neutral": 0.0,
    }


def _renormalize(scores: dict[str, float]) -> dict[str, float]:
    total = sum(max(value, 0.0) for value in scores.values())
    if total <= 0:
        return {label: round(1.0 / len(scores), 4) for label in scores}
    return {label: round(max(value, 0.0) / total, 4) for label, value in scores.items()}


def fuse_modalities(
    *,
    text_rows: list[dict[str, Any]],
    audio_rows: list[dict[str, Any]],
    video_rows: list[dict[str, Any]],
    output_dir: Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    audio_by_id = {str(row["segment_id"]): row for row in audio_rows}
    video_by_id = {str(row["segment_id"]): row for row in video_rows}
    rows: list[dict[str, Any]] = []
    for text_row in text_rows:
        segment_id = str(text_row["segment_id"])
        scores = dict(text_row.get("signal_probabilities") or {})
        for label, value in _audio_adjustment(audio_by_id.get(segment_id)).items():
            scores[label] = float(scores.get(label, 0.0)) + value
        for label, value in _video_adjustment(video_by_id.get(segment_id)).items():
            scores[label] = float(scores.get(label, 0.0)) + value
        fused_probabilities = _renormalize(scores)
        fused_signal = max(fused_probabilities, key=fused_probabilities.get)
        confidence = float(fused_probabilities[fused_signal])
        rows.append(
            {
                "segment_id": segment_id,
                "fusion_model": "weighted_text_anchor_v1",
                "candidate_models": ["LogisticRegression", "RandomForest", "shallow_pytorch_nn"],
                "trained_model_used": False,
                "text_anchor_signal": text_row.get("rule_signal"),
                "fused_signal": fused_signal,
                "fused_probabilities": fused_probabilities,
                "confidence": round(confidence, 4),
                "uncertainty": round(1.0 - confidence, 4),
                "feature_sources": {
                    "text": True,
                    "audio": bool(audio_by_id.get(segment_id, {}).get("available")),
                    "video": bool(video_by_id.get(segment_id, {}).get("available")),
                },
            }
        )
    status = {
        "stage": "fusion",
        "status": "completed",
        "dry_run": dry_run,
        "rows": len(rows),
        "notes": ["Fusion keeps text as anchor and treats audio/video as bounded adjustments."],
    }
    if not dry_run:
        write_jsonl(output_dir / "fusion_predictions.jsonl", rows)
        write_json(output_dir / "fusion_status.json", status)
    return {"rows": rows, "status": status}
