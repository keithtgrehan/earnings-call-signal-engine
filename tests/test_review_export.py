from __future__ import annotations

import pytest

from review.export_gold import ReviewExportError, dedup_key, export_gold_labels, validate_reviewed_row


def reviewed_row(**overrides):
    row = {
        "case_id": "NVDA_2026_Q4",
        "chunk_id": "chunk-1",
        "text": "Management raised guidance.",
        "labels": ["guidance_revision"],
        "source": "argilla_review",
        "reviewer": "reviewer_a",
        "review_timestamp": "2026-01-01T00:00:00Z",
        "review_state": "reviewed",
        "metadata": {"section": "prepared_remarks"},
        "provenance": {"source_file": "fixture"},
    }
    row.update(overrides)
    return row


def test_validate_reviewed_row_rejects_unreviewed_suggestions() -> None:
    with pytest.raises(ReviewExportError):
        validate_reviewed_row(reviewed_row(review_state="suggested"))


def test_validate_reviewed_row_rejects_empty_labels() -> None:
    with pytest.raises(ReviewExportError):
        validate_reviewed_row(reviewed_row(labels=[]))


def test_export_dedupes_by_case_chunk_label_text_hash() -> None:
    rows, rejected = export_gold_labels([reviewed_row(), reviewed_row()], mode="merge")
    assert len(rows) == 1
    assert rejected == []
    assert dedup_key(rows[0])


def test_export_merge_preserves_existing_and_adds_new() -> None:
    existing = [reviewed_row(chunk_id="existing")]
    rows, rejected = export_gold_labels([reviewed_row(chunk_id="new")], existing_rows=existing, mode="merge")
    assert len(rows) == 2
    assert rejected == []


def test_rejected_rows_are_returned_not_promoted() -> None:
    rows, rejected = export_gold_labels([reviewed_row(review_state="rejected")], mode="new")
    assert rows == []
    assert rejected and "not explicitly" in rejected[0]["reason"]
