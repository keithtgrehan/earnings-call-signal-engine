from __future__ import annotations

from review.review_queue import build_review_queue, workload_summary


def test_top_risk_queue_prioritizes_low_confidence_guidance_pressure() -> None:
    records = [
        {"case_id": "A", "chunk_id": "c1", "text": "Analyst question about guidance uncertainty and pricing pressure."},
        {"case_id": "A", "chunk_id": "c2", "text": "Routine opening remarks."},
    ]
    suggestions = [{"case_id": "A", "chunk_id": "c1", "label": "guidance_revision", "confidence": 0.55}]
    queue = build_review_queue(records, suggestions)
    assert queue[0]["chunk_id"] == "c1"
    assert "low_confidence" in queue[0]["priority_reasons"]


def test_queue_sampling_modes_are_stable() -> None:
    records = [{"case_id": "A", "chunk_id": f"c{i}", "text": "guidance"} for i in range(6)]
    suggestions = [{"case_id": "A", "chunk_id": f"c{i}", "label": "uncertainty", "confidence": 0.8} for i in range(6)]
    first = build_review_queue(records, suggestions, mode="random", seed=7)
    second = build_review_queue(records, suggestions, mode="random", seed=7)
    assert [row["chunk_id"] for row in first] == [row["chunk_id"] for row in second]
    assert len(build_review_queue(records, suggestions, mode="stratified", limit=3)) == 3


def test_workload_summary_counts_labels() -> None:
    queue = [{"suggested_labels": "uncertainty;guidance_revision"}, {"suggested_labels": ""}]
    summary = workload_summary(queue)
    assert summary["total_review_items"] == 2
    assert summary["label_coverage"]["uncertainty"] == 1
