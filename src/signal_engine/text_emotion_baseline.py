from __future__ import annotations

from collections.abc import Iterable
import re
from typing import Any


EMOTION_LABELS: tuple[str, ...] = (
    "anger",
    "frustration",
    "confusion",
    "satisfaction",
    "neutral",
    "concern",
    "urgency",
)

_LABEL_PRIORITY: tuple[str, ...] = (
    "urgency",
    "anger",
    "frustration",
    "concern",
    "confusion",
    "satisfaction",
    "neutral",
)
_TOKEN_BOUNDARY = re.compile(r"[^a-z0-9]+")
_KEYWORD_WEIGHTS: dict[str, tuple[tuple[str, float], ...]] = {
    "anger": (
        ("angry", 2.5),
        ("furious", 3.0),
        ("outraged", 3.0),
        ("unacceptable", 1.7),
        ("ridiculous", 1.7),
        ("fed up", 2.0),
        ("canceled without notice", 2.1),
        ("charged the wrong card", 2.0),
    ),
    "frustration": (
        ("frustrated", 2.5),
        ("still waiting", 1.8),
        ("keep reopening", 2.0),
        ("again", 0.8),
        ("no update", 1.5),
        ("stuck", 1.4),
        ("same issue", 1.6),
        ("nothing has changed", 1.7),
    ),
    "confusion": (
        ("confused", 2.5),
        ("not sure", 1.8),
        ("don't understand", 2.0),
        ("do not understand", 2.0),
        ("which version", 1.8),
        ("can you explain", 1.4),
        ("why did", 1.0),
        ("what does", 1.1),
        ("unclear", 1.6),
    ),
    "satisfaction": (
        ("thank you", 1.8),
        ("thanks", 1.4),
        ("appreciate", 1.8),
        ("happy", 2.2),
        ("pleased", 2.0),
        ("that works", 1.6),
        ("solved", 1.8),
        ("resolved", 1.8),
        ("great", 1.2),
    ),
    "neutral": (
        ("for reference", 1.3),
        ("sharing the update", 1.3),
        ("the current status", 1.1),
        ("scheduled for", 1.0),
        ("the meeting starts", 1.0),
        ("attached is", 1.0),
        ("noted", 1.0),
    ),
    "concern": (
        ("concerned", 2.4),
        ("worried", 2.1),
        ("risk", 1.2),
        ("might slip", 1.8),
        ("may slip", 1.8),
        ("haven't confirmed", 1.6),
        ("have not confirmed", 1.6),
        ("could impact", 1.5),
        ("exposed", 1.2),
        ("issue remains", 1.4),
    ),
    "urgency": (
        ("urgent", 2.5),
        ("asap", 2.3),
        ("today", 1.6),
        ("immediately", 2.1),
        ("right away", 2.0),
        ("before the board call", 2.7),
        ("before launch", 2.3),
        ("need this fixed", 2.2),
        ("by end of day", 2.2),
        ("deadline", 1.5),
    ),
}


def _normalize_text(text: Any) -> str:
    lowered = str(text or "").strip().lower()
    return re.sub(r"\s+", " ", lowered)


def _normalize_allowed_labels(
    allowed_labels: Iterable[str] | None,
) -> tuple[str, ...]:
    if allowed_labels is None:
        return EMOTION_LABELS
    normalized = tuple(label for label in allowed_labels if label in EMOTION_LABELS)
    if not normalized:
        raise ValueError(
            f"allowed_labels must contain at least one supported label from {EMOTION_LABELS}."
        )
    return normalized


def _has_keyword(text: str, keyword: str) -> bool:
    normalized_keyword = keyword.lower()
    if " " in normalized_keyword:
        return normalized_keyword in text
    tokenized_text = f" {_TOKEN_BOUNDARY.sub(' ', text)} "
    return f" {normalized_keyword} " in tokenized_text


def _score_label(text: str, label: str) -> tuple[float, list[str]]:
    score = 0.0
    evidence_terms: list[str] = []
    for keyword, weight in _KEYWORD_WEIGHTS[label]:
        if _has_keyword(text, keyword):
            score += weight
            evidence_terms.append(keyword)
    return score, evidence_terms


def classify_text_emotion(
    text: str,
    allowed_labels: Iterable[str] | None = None,
) -> dict[str, Any]:
    normalized_text = _normalize_text(text)
    candidate_labels = _normalize_allowed_labels(allowed_labels)

    if not normalized_text:
        return {
            "label": "neutral" if "neutral" in candidate_labels else candidate_labels[0],
            "confidence": 0.35,
            "evidence_terms": [],
            "method": "deterministic_keyword_baseline",
        }

    label_scores: dict[str, float] = {}
    label_evidence: dict[str, list[str]] = {}
    for label in candidate_labels:
        score, evidence_terms = _score_label(normalized_text, label)
        label_scores[label] = score
        label_evidence[label] = evidence_terms

    best_label = "neutral" if "neutral" in candidate_labels else candidate_labels[0]
    best_score = label_scores.get(best_label, 0.0)
    best_evidence = label_evidence.get(best_label, [])

    for label in _LABEL_PRIORITY:
        if label not in candidate_labels:
            continue
        score = label_scores[label]
        evidence_terms = label_evidence[label]
        if score > best_score:
            best_label = label
            best_score = score
            best_evidence = evidence_terms
            continue
        if score == best_score and len(evidence_terms) > len(best_evidence):
            best_label = label
            best_evidence = evidence_terms

    if best_score <= 0.0:
        best_label = "neutral" if "neutral" in candidate_labels else candidate_labels[0]
        best_evidence = []
        confidence = 0.42 if best_label == "neutral" else 0.34
    else:
        total_score = sum(max(score, 0.0) for score in label_scores.values())
        confidence = best_score / total_score if total_score else 0.0
        confidence = max(0.55, min(0.95, confidence + (0.03 * len(best_evidence))))

    return {
        "label": best_label,
        "confidence": round(confidence, 4),
        "evidence_terms": best_evidence,
        "method": "deterministic_keyword_baseline",
    }


def batch_classify(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    predictions: list[dict[str, Any]] = []
    for record in records:
        allowed_labels = record.get("allowed_labels")
        prediction = classify_text_emotion(
            str(record.get("text", "")),
            allowed_labels=allowed_labels if isinstance(allowed_labels, list) else None,
        )
        predictions.append(
            {
                "case_id": record.get("case_id"),
                "domain": record.get("domain"),
                "text": record.get("text"),
                "gold_label": record.get("gold_label"),
                "allowed_labels": allowed_labels,
                **prediction,
            }
        )
    return predictions


__all__ = [
    "EMOTION_LABELS",
    "batch_classify",
    "classify_text_emotion",
]
