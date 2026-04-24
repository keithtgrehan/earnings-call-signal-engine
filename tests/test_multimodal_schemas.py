from __future__ import annotations

from signal_engine.multimodal.schemas import (
    EvidenceSpan,
    EvidenceWindow,
    FusedSignal,
    ModalityFeatureSet,
    MultimodalSignalReport,
    SignalFeature,
)


def test_multimodal_schema_objects_serialize_cleanly() -> None:
    span = EvidenceSpan(text="may slip", start_char=10, end_char=18)
    window = EvidenceWindow(start_seconds=0.0, end_seconds=3.5, description="opening turn")
    feature = SignalFeature(
        signal_name="uncertainty",
        modality="transcript",
        strength="medium",
        confidence=0.61,
        reason="Matched hedge language.",
        recommended_review_action="Review dates and commitments.",
        evidence_span=span,
        measurements={"match_count": 2},
    )
    feature_set = ModalityFeatureSet(
        modality="transcript",
        available=True,
        source_path="sample.txt",
        measurements={"token_count": 8},
        signals=[feature],
        limitations=["review cue only"],
    )
    fused = FusedSignal(
        signal_name="uncertainty_review",
        modalities=["transcript"],
        strength="medium",
        confidence=0.61,
        reason="Transcript evidence is primary.",
        recommended_review_action="Review hedged language.",
        evidence_spans=[span],
        evidence_windows=[window],
    )
    report = MultimodalSignalReport(
        input_metadata={"domain": "support"},
        modality_feature_sets={"transcript": feature_set},
        fused_signals=[fused],
        limitations=["transcript-first canonical"],
    )

    payload = report.to_dict()
    assert payload["input_metadata"]["domain"] == "support"
    assert payload["modality_feature_sets"]["transcript"]["available"] is True
    assert payload["fused_signals"][0]["signal_name"] == "uncertainty_review"
