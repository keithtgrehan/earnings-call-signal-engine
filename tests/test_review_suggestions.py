from __future__ import annotations

from review.suggestions import build_suggestions, labels_from_weak_row


def test_suggestion_mapping_from_event_fields() -> None:
    labels = labels_from_weak_row(
        {
            "guidance_related": True,
            "pushback_flag": True,
            "uncertainty_flag": True,
            "sentiment": "NEGATIVE",
        }
    )
    assert labels == ["analyst_pressure", "guidance_revision", "negative_surprise", "uncertainty"]


def test_confidence_filtering_and_missing_labels() -> None:
    rows = [
        {"case_id": "A", "chunk_id": "c1", "weak_label": "guidance", "confidence": 0.7},
        {"case_id": "A", "chunk_id": "c2", "weak_label": "uncertainty", "confidence": 0.2},
        {"case_id": "A", "chunk_id": "c3", "confidence": 0.9},
    ]
    suggestions = build_suggestions(rows, min_confidence=0.6)
    assert [item.label for item in suggestions] == ["guidance_revision"]
    assert suggestions[0].chunk_id == "c1"


def test_suggestions_are_records_not_truth() -> None:
    suggestion = build_suggestions([{"case_id": "A", "chunk_id": "c1", "label": "positive_surprise", "confidence": 0.9}])[0].to_record()
    assert suggestion["label"] == "positive_surprise"
    assert "review_state" not in suggestion
