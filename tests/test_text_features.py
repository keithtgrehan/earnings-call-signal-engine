from __future__ import annotations

from signal_engine.multimodal.text_features import extract_text_feature_set


def test_extract_text_feature_set_surfaces_expected_review_cues() -> None:
    feature_set = extract_text_feature_set(
        "We may slip this quarter, but I will send the recovery plan today if finance approves it.",
        domain="account_management",
        source_path="fixture.txt",
    )

    signal_names = {signal.signal_name for signal in feature_set.signals}
    assert feature_set.available is True
    assert "uncertainty" in signal_names or "hedging" in signal_names
    assert "reassurance" in signal_names
    assert feature_set.measurements["token_count"] > 0
