from __future__ import annotations

import random
from collections import Counter
from typing import Any

from .suggestions import SIGNALS, suggestions_by_chunk


GUIDANCE_TERMS = ("guidance", "outlook", "forecast", "raise", "lower", "revised")
PRESSURE_TERMS = ("analyst", "question", "margin", "demand", "competition", "pricing")
UNCERTAINTY_TERMS = ("uncertain", "volatility", "macro", "headwind", "risk", "maybe", "could")


def priority_score(record: dict[str, Any], suggestions: list[dict[str, Any]] | None = None, label_counts: Counter[str] | None = None) -> tuple[float, list[str]]:
    suggestions = suggestions or []
    label_counts = label_counts or Counter()
    text = str(record.get("text") or "").lower()
    score = 0.0
    reasons: list[str] = []
    confidences = [float(s.get("confidence") or 0.0) for s in suggestions]
    labels = [str(s.get("label") or "") for s in suggestions]
    if not suggestions:
        score += 5
        reasons.append("unlabeled")
    if confidences and min(confidences) < 0.7:
        score += 3
        reasons.append("low_confidence")
    if len(set(labels)) >= 2:
        score += 3
        reasons.append("conflicting_or_multi_signal")
    if any(term in text for term in GUIDANCE_TERMS):
        score += 2
        reasons.append("guidance_language")
    if any(term in text for term in PRESSURE_TERMS):
        score += 2
        reasons.append("analyst_pressure")
    if any(term in text for term in UNCERTAINTY_TERMS):
        score += 2
        reasons.append("uncertainty_cluster")
    for label in set(labels):
        if label in SIGNALS and label_counts[label] <= 2:
            score += 1
            reasons.append(f"rare_{label}")
    return score, reasons or ["coverage"]


def build_review_queue(
    records: list[dict[str, Any]],
    suggestions: list[dict[str, Any]],
    *,
    mode: str = "top-risk",
    limit: int | None = None,
    seed: int = 13,
) -> list[dict[str, Any]]:
    grouped = suggestions_by_chunk(suggestions)
    label_counts = Counter(str(s.get("label") or "") for s in suggestions)
    queue: list[dict[str, Any]] = []
    for record in records:
        chunk_id = str(record.get("chunk_id") or record.get("id") or "")
        chunk_suggestions = grouped.get(chunk_id, [])
        score, reasons = priority_score(record, chunk_suggestions, label_counts)
        queue.append(
            {
                "rank": 0,
                "case_id": record.get("case_id") or record.get("metadata", {}).get("case_id", ""),
                "chunk_id": chunk_id,
                "priority_score": round(score, 4),
                "priority_reasons": ";".join(reasons),
                "suggested_labels": ";".join(sorted({str(s.get("label")) for s in chunk_suggestions if s.get("label")})),
                "suggestion_count": len(chunk_suggestions),
                "text_preview": str(record.get("text") or "")[:240].replace("\n", " "),
            }
        )
    if mode == "random":
        rng = random.Random(seed)
        rng.shuffle(queue)
    elif mode == "stratified":
        queue = _stratified(queue)
    else:
        queue.sort(key=lambda row: (-float(row["priority_score"]), str(row["case_id"]), str(row["chunk_id"])))
    if limit is not None:
        queue = queue[:limit]
    for idx, row in enumerate(queue, start=1):
        row["rank"] = idx
    return queue


def _stratified(queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    for row in sorted(queue, key=lambda item: -float(item["priority_score"])):
        key = str(row.get("suggested_labels") or "unlabeled").split(";")[0] or "unlabeled"
        buckets.setdefault(key, []).append(row)
    ordered: list[dict[str, Any]] = []
    while any(buckets.values()):
        for key in sorted(buckets):
            if buckets[key]:
                ordered.append(buckets[key].pop(0))
    return ordered


def workload_summary(queue: list[dict[str, Any]]) -> dict[str, Any]:
    label_counts: Counter[str] = Counter()
    for row in queue:
        labels = str(row.get("suggested_labels") or "unlabeled").split(";")
        for label in labels:
            label_counts[label or "unlabeled"] += 1
    return {
        "total_review_items": len(queue),
        "estimated_minutes_at_45_seconds_each": round(len(queue) * 45 / 60, 2),
        "label_coverage": dict(sorted(label_counts.items())),
    }
