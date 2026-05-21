from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


SIGNALS = [
    "guidance_revision",
    "tone_shift",
    "analyst_pressure",
    "uncertainty",
    "evasive_answer",
    "positive_surprise",
    "negative_surprise",
]

SIGNAL_ALIASES = {
    "guidance": "guidance_revision",
    "guidance_related": "guidance_revision",
    "tone": "tone_shift",
    "tone_shift": "tone_shift",
    "analyst_pressure": "analyst_pressure",
    "pushback": "analyst_pressure",
    "pushback_flag": "analyst_pressure",
    "uncertainty": "uncertainty",
    "uncertainty_flag": "uncertainty",
    "evasive": "evasive_answer",
    "evasive_answer": "evasive_answer",
    "positive": "positive_surprise",
    "positive_surprise": "positive_surprise",
    "negative": "negative_surprise",
    "negative_surprise": "negative_surprise",
}


@dataclass(frozen=True)
class ReviewSuggestion:
    chunk_id: str
    case_id: str
    label: str
    confidence: float
    evidence_start: int | None
    evidence_end: int | None
    rule_source: str
    metadata: dict[str, Any]

    def to_record(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "case_id": self.case_id,
            "label": self.label,
            "confidence": round(float(self.confidence), 6),
            "evidence_start": self.evidence_start,
            "evidence_end": self.evidence_end,
            "rule_source": self.rule_source,
            "metadata": self.metadata,
        }


def _confidence(row: dict[str, Any]) -> float:
    for key in ("confidence", "score", "signed_score"):
        if key in row and row.get(key) not in ("", None):
            try:
                return max(0.0, min(1.0, abs(float(row[key]))))
            except (TypeError, ValueError):
                continue
    return 0.5


def _canonical_label(value: Any) -> str | None:
    text = str(value or "").strip().lower()
    if not text:
        return None
    return SIGNAL_ALIASES.get(text, text if text in SIGNALS else None)


def labels_from_weak_row(row: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    for key in ("weak_label", "label", "signal", "signal_type", "signal_family"):
        label = _canonical_label(row.get(key))
        if label:
            labels.append(label)
    sentiment = str(row.get("sentiment") or "").lower()
    signed_score = row.get("signed_score")
    if sentiment == "positive":
        labels.append("positive_surprise")
    elif sentiment == "negative":
        labels.append("negative_surprise")
    elif signed_score not in (None, ""):
        try:
            score = float(signed_score)
            if score >= 0.4:
                labels.append("positive_surprise")
            elif score <= -0.4:
                labels.append("negative_surprise")
        except (TypeError, ValueError):
            pass
    for key, label in (("guidance_related", "guidance_revision"), ("pushback_flag", "analyst_pressure"), ("uncertainty_flag", "uncertainty")):
        if row.get(key) is True or str(row.get(key)).strip().lower() == "true":
            labels.append(label)
    if row.get("evasive_answer") is True or str(row.get("evasive_answer")).strip().lower() == "true":
        labels.append("evasive_answer")
    if row.get("tone_shift") is True or str(row.get("tone_shift")).strip().lower() == "true":
        labels.append("tone_shift")
    return sorted(set(label for label in labels if label in SIGNALS))


def build_suggestions(rows: Iterable[dict[str, Any]], *, min_confidence: float = 0.6) -> list[ReviewSuggestion]:
    suggestions: list[ReviewSuggestion] = []
    for row in rows:
        confidence = _confidence(row)
        if confidence < min_confidence:
            continue
        chunk_id = str(row.get("chunk_id") or row.get("object_id") or row.get("candidate_id") or "")
        case_id = str(row.get("case_id") or "")
        for label in labels_from_weak_row(row):
            suggestions.append(
                ReviewSuggestion(
                    chunk_id=chunk_id,
                    case_id=case_id,
                    label=label,
                    confidence=confidence,
                    evidence_start=_int_or_none(row.get("evidence_start") or row.get("start")),
                    evidence_end=_int_or_none(row.get("evidence_end") or row.get("end")),
                    rule_source=str(row.get("rule_source") or row.get("source_artifact") or "deterministic"),
                    metadata={k: v for k, v in row.items() if k not in {"text"}},
                )
            )
    return suggestions


def suggestions_by_chunk(suggestions: Iterable[ReviewSuggestion | dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in suggestions:
        row = item.to_record() if isinstance(item, ReviewSuggestion) else dict(item)
        grouped.setdefault(str(row.get("chunk_id") or ""), []).append(row)
    return grouped


def _int_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None
