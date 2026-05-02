from __future__ import annotations

from pathlib import Path
from typing import Any

from data_layer.io import write_json, write_jsonl
from data_layer.schemas import SegmentRecord
from signal_engine.evaluation_backbone import top_two_margin
from signal_engine.signal_baseline import SIGNAL_FAMILY_LABELS, predict_deterministic_signal_family
from signal_engine.text_emotion_baseline import classify_text_emotion

from .weak_supervision import weak_label_segment


def _probabilities(label: str, confidence: float, labels: tuple[str, ...]) -> dict[str, float]:
    fallback = max(0.0, 1.0 - confidence)
    other_count = max(len(labels) - 1, 1)
    return {
        candidate: round(confidence if candidate == label else fallback / other_count, 4)
        for candidate in labels
    }


def _sentiment_from_emotion(emotion: str, confidence: float) -> dict[str, Any]:
    if emotion in {"satisfaction"}:
        label = "positive"
    elif emotion in {"anger", "frustration", "concern", "urgency"}:
        label = "negative"
    else:
        label = "neutral"
    return {"label": label, "confidence": round(confidence, 4)}


def score_text_segments(
    segments: list[SegmentRecord],
    *,
    output_dir: Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for segment in segments:
        rule = predict_deterministic_signal_family(segment.text, domain=segment.domain)
        weak = weak_label_segment(segment.text, domain=segment.domain)
        emotion = classify_text_emotion(segment.text)
        signal_confidence = 0.72 if rule.get("evidence_terms") else 0.44
        signal_label = str(rule["label"])
        signal_probabilities = _probabilities(signal_label, signal_confidence, SIGNAL_FAMILY_LABELS)
        sentiment = _sentiment_from_emotion(str(emotion["label"]), float(emotion["confidence"]))
        rows.append(
            {
                "segment_id": segment.segment_id,
                "record_id": segment.record_id,
                "domain": segment.domain,
                "text": segment.text,
                "rule_signal": signal_label,
                "snorkel_label": weak["label"],
                "baseline_signal": signal_label,
                "transformer_signal": None,
                "finbert_signal": None,
                "signal_probabilities": signal_probabilities,
                "signal_confidence": signal_confidence,
                "signal_uncertainty": round(1.0 - signal_confidence, 4),
                "signal_margin": top_two_margin(signal_probabilities),
                "emotion": emotion["label"],
                "emotion_confidence": emotion["confidence"],
                "sentiment": sentiment["label"],
                "sentiment_confidence": sentiment["confidence"],
                "evidence": {
                    "rule_terms": rule.get("evidence_terms", []),
                    "weak_supervision_reason": weak.get("reason", ""),
                    "emotion_terms": emotion.get("evidence_terms", []),
                },
                "methods": {
                    "rule": "deterministic_signal_baseline",
                    "weak_supervision": weak["method"],
                    "baseline_classifier": "deterministic_smoke_fallback",
                    "transformer": "optional_adapter_not_run",
                    "finbert": "optional_adapter_not_run",
                },
            }
        )

    status = {
        "stage": "text",
        "status": "completed",
        "dry_run": dry_run,
        "segments": len(segments),
        "scored_rows": len(rows),
        "notes": ["Deterministic text rules anchor all v1 predictions; transformer adapters are optional."],
    }
    if not dry_run:
        write_jsonl(output_dir / "text_predictions.jsonl", rows)
        write_json(output_dir / "text_status.json", status)
    return {"rows": rows, "status": status}
