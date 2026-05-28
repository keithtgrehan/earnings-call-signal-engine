from __future__ import annotations

import pytest

from signal_engine.audio.features import neutral_audio_feature_row


def test_audio_features_are_neutral_metadata_only() -> None:
    row = neutral_audio_feature_row(case_id="case1", audio_sha256="sha256:" + "a" * 64, feature_name="pause_duration", value="1.2")

    assert row["label_type"] == "neutral_metadata"
    assert row["emotion_label"] is False
    assert row["deception_label"] is False
    assert row["stress_label"] is False


def test_audio_features_reject_emotion_like_feature() -> None:
    with pytest.raises(ValueError):
        neutral_audio_feature_row(case_id="case1", audio_sha256="sha256:" + "a" * 64, feature_name="emotion")
