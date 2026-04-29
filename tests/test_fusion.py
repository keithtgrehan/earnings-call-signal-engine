from __future__ import annotations

from signal_engine.multimodal.fusion import build_multimodal_report
from signal_engine.multimodal.schemas import ModalityFeatureSet, SignalFeature
from signal_engine.multimodal.text_features import extract_text_feature_set


def test_fusion_preserves_transcript_anchor_and_caps_confidence() -> None:
    transcript = extract_text_feature_set(
        "We may slip the quarter and finance is pushing for a firmer answer.",
        domain="earnings",
    )
    audio = ModalityFeatureSet(
        modality="audio",
        available=True,
        measurements={"silence_ratio": 0.2},
        signals=[
            SignalFeature(
                signal_name="pause_length",
                modality="audio",
                strength="low",
                confidence=0.44,
                reason="Pause proxy",
                recommended_review_action="Review audio manually.",
            )
        ],
    )
    report = build_multimodal_report(
        input_metadata={"domain": "earnings"},
        feature_sets={
            "transcript": transcript,
            "audio": audio,
            "video": ModalityFeatureSet(modality="video", available=False, limitations=["not provided"]),
        },
    )

    assert report.fused_signals
    assert any(signal.modalities[0] == "audio" or "transcript" in signal.modalities for signal in report.fused_signals)
    assert all(signal.confidence <= 0.82 for signal in report.fused_signals)


def test_fusion_does_not_upgrade_side_cues_to_high_confidence_without_transcript() -> None:
    audio_only = ModalityFeatureSet(
        modality="audio",
        available=True,
        signals=[
            SignalFeature(
                signal_name="pause_length",
                modality="audio",
                strength="low",
                confidence=0.5,
                reason="pause proxy",
                recommended_review_action="review manually",
            )
        ],
    )
    report = build_multimodal_report(
        input_metadata={"domain": "support"},
        feature_sets={
            "transcript": ModalityFeatureSet(modality="transcript", available=False, limitations=["missing"]),
            "audio": audio_only,
            "video": ModalityFeatureSet(modality="video", available=False, limitations=["missing"]),
        },
    )

    assert report.fused_signals
    assert all(signal.confidence <= 0.42 for signal in report.fused_signals)
    assert all(signal.strength != "high" for signal in report.fused_signals)
