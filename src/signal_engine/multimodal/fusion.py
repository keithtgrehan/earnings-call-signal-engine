from __future__ import annotations

from typing import Iterable

from .schemas import (
    FusedSignal,
    ModalityFeatureSet,
    MultimodalSignalReport,
    SignalFeature,
)


FUSION_BUCKETS = {
    "uncertainty": "uncertainty_review",
    "hedging": "uncertainty_review",
    "pressure": "friction_review",
    "escalation_risk": "friction_review",
    "contradiction": "contradiction_review",
    "reassurance": "reassurance_review",
    "pause_length": "uncertainty_review",
    "volume_intensity_change": "friction_review",
    "motion_change_proxy": "friction_review",
}

RECOMMENDED_ACTIONS = {
    "uncertainty_review": "Review cautious or ambiguous language before making a directional judgment.",
    "friction_review": "Check the underlying turns and media cues before escalating severity.",
    "contradiction_review": "Compare apparently conflicting statements directly in the transcript.",
    "reassurance_review": "Verify whether reassuring language is backed by owners, dates, and concrete evidence.",
}


def _bucket_strength(features: list[SignalFeature], *, text_anchor: bool) -> str:
    strengths = {item.strength for item in features}
    if text_anchor and "high" in strengths and len(features) >= 2:
        return "high"
    if "high" in strengths or "medium" in strengths:
        return "medium"
    return "low"


def _bucket_confidence(features: list[SignalFeature], *, text_anchor: bool) -> float:
    base = max(item.confidence for item in features)
    if not text_anchor:
        return min(base, 0.42)
    strong_support = sum(1 for item in features if item.confidence >= 0.45)
    if strong_support >= 2:
        return min(0.82, base + 0.05)
    return min(0.78, base)


def fuse_feature_sets(feature_sets: Iterable[ModalityFeatureSet]) -> list[FusedSignal]:
    grouped: dict[str, list[SignalFeature]] = {}
    for feature_set in feature_sets:
        if not feature_set.available:
            continue
        for signal in feature_set.signals:
            bucket = FUSION_BUCKETS.get(signal.signal_name)
            if bucket is None:
                continue
            grouped.setdefault(bucket, []).append(signal)

    fused_signals: list[FusedSignal] = []
    for bucket, features in grouped.items():
        modalities = sorted({feature.modality for feature in features})
        text_anchor = any(feature.modality == "transcript" for feature in features)
        reason_prefix = (
            "Transcript evidence is primary and is supported by optional side cues."
            if text_anchor and len(modalities) > 1
            else "Transcript evidence is primary for this review cue."
            if text_anchor
            else "Only supporting side cues were available, so confidence stays bounded."
        )
        supporting_measurements = {
            feature.modality: feature.measurements for feature in features if feature.measurements
        }
        fused_signals.append(
            FusedSignal(
                signal_name=bucket,
                modalities=modalities,
                strength=_bucket_strength(features, text_anchor=text_anchor),
                confidence=_bucket_confidence(features, text_anchor=text_anchor),
                reason=f"{reason_prefix} Modalities: {', '.join(modalities)}.",
                recommended_review_action=RECOMMENDED_ACTIONS[bucket],
                evidence_spans=[
                    feature.evidence_span for feature in features if feature.evidence_span is not None
                ],
                evidence_windows=[
                    feature.evidence_window for feature in features if feature.evidence_window is not None
                ],
                supporting_measurements=supporting_measurements,
            )
        )
    return sorted(fused_signals, key=lambda item: (item.signal_name, item.confidence), reverse=True)


def build_multimodal_report(
    *,
    input_metadata: dict[str, object],
    feature_sets: dict[str, ModalityFeatureSet],
) -> MultimodalSignalReport:
    missing_modalities = [
        modality for modality, feature_set in feature_sets.items() if not feature_set.available
    ]
    limitations = [
        "Transcript-first deterministic evidence remains canonical.",
        "Signals are review cues, not claims about hidden emotion, truthfulness, or diagnosis.",
    ]
    if missing_modalities:
        limitations.append(f"Missing or unsupported modalities: {', '.join(missing_modalities)}.")

    return MultimodalSignalReport(
        input_metadata=input_metadata,
        modality_feature_sets=feature_sets,
        fused_signals=fuse_feature_sets(feature_sets.values()),
        limitations=limitations,
    )


__all__ = ["build_multimodal_report", "fuse_feature_sets"]
