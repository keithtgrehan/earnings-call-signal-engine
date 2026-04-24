from __future__ import annotations

import re
from collections import Counter
from typing import Iterable

from .schemas import Evidence, TranscriptSegment

TOKEN_RE = re.compile(r"[a-zA-Z0-9']+")
DATE_OR_DEADLINE_RE = re.compile(
    r"\b(today|tomorrow|monday|tuesday|wednesday|thursday|friday|next week|next month|by [a-z]+|\d{1,2}/\d{1,2})\b",
    re.IGNORECASE,
)
OWNER_COMMITMENT_RE = re.compile(
    r"\b(i|we|owner|team|manager|rep|account manager)\s+(will|can|own|send|share|schedule|deliver|review|confirm)\b",
    re.IGNORECASE,
)

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "for",
    "from",
    "how",
    "i",
    "if",
    "in",
    "is",
    "it",
    "my",
    "of",
    "on",
    "or",
    "our",
    "the",
    "to",
    "we",
    "what",
    "when",
    "with",
    "you",
    "your",
}


def normalize_text(text: str) -> str:
    return " ".join(text.split()).strip()


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def content_tokens(text: str) -> list[str]:
    return [token for token in tokenize(text) if token not in STOPWORDS]


def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def bounded_score(count: int, *, cap: int = 3) -> float:
    return round(clamp(safe_ratio(count, cap)), 4)


def term_found(text: str, term: str) -> bool:
    normalized_text = normalize_text(text).lower()
    normalized_term = term.lower()
    if " " in normalized_term:
        return normalized_term in normalized_text
    return re.search(rf"\b{re.escape(normalized_term)}\b", normalized_text) is not None


def excerpt(text: str, term: str, *, width: int = 160) -> str:
    normalized = normalize_text(text)
    lowered = normalized.lower()
    start = lowered.find(term.lower())
    if start < 0:
        return normalized[:width]
    left = max(0, start - 30)
    right = min(len(normalized), start + len(term) + 90)
    snippet = normalized[left:right]
    if left > 0:
        snippet = f"...{snippet}"
    if right < len(normalized):
        snippet = f"{snippet}..."
    return snippet


def evidence_for_terms(
    segments: Iterable[TranscriptSegment],
    terms: Iterable[str],
    *,
    signal_name: str,
    reason: str,
    roles: set[str] | None = None,
    limit: int = 5,
) -> list[Evidence]:
    evidence: list[Evidence] = []
    seen: set[tuple[int | None, str]] = set()
    term_list = list(terms)
    for segment in segments:
        if roles is not None and segment.role not in roles:
            continue
        for term in term_list:
            if not term_found(segment.text, term):
                continue
            key = (segment.message_index, term.lower())
            if key in seen:
                continue
            evidence.append(
                Evidence(
                    signal_name=signal_name,
                    message_index=segment.message_index,
                    matched_text=excerpt(segment.text, term),
                    reason=reason,
                )
            )
            seen.add(key)
            if len(evidence) >= limit:
                return evidence
    return evidence


def evidence_for_pattern(
    segments: Iterable[TranscriptSegment],
    pattern: re.Pattern[str],
    *,
    signal_name: str,
    reason: str,
    roles: set[str] | None = None,
    limit: int = 5,
) -> list[Evidence]:
    evidence: list[Evidence] = []
    for segment in segments:
        if roles is not None and segment.role not in roles:
            continue
        match = pattern.search(segment.text)
        if match is None:
            continue
        evidence.append(
            Evidence(
                signal_name=signal_name,
                message_index=segment.message_index,
                matched_text=excerpt(segment.text, match.group(0)),
                reason=reason,
            )
        )
        if len(evidence) >= limit:
            return evidence
    return evidence


def token_overlap_ratio(left: str, right: str) -> float:
    left_tokens = set(content_tokens(left))
    right_tokens = set(content_tokens(right))
    if not left_tokens:
        return 0.0
    return safe_ratio(len(left_tokens & right_tokens), len(left_tokens))


def count_term_hits(text: str, terms: Iterable[str]) -> int:
    return sum(1 for term in terms if term_found(text, term))


def token_count_by_segments(segments: Iterable[TranscriptSegment]) -> int:
    return sum(len(tokenize(segment.text)) for segment in segments)


def sentiment_proxy_score(
    segments: Iterable[TranscriptSegment],
    *,
    positive_terms: Iterable[str],
    negative_terms: Iterable[str],
) -> float:
    positive_hits = 0
    negative_hits = 0
    for segment in segments:
        positive_hits += count_term_hits(segment.text, positive_terms)
        negative_hits += count_term_hits(segment.text, negative_terms)
    score = safe_ratio(positive_hits + 1, positive_hits + negative_hits + 2)
    return round(clamp(score), 4)


def lexical_density(text: str) -> float:
    tokens = tokenize(text)
    if not tokens:
        return 0.0
    frequencies = Counter(tokens)
    unique_tokens = len(frequencies)
    return round(clamp(safe_ratio(unique_tokens, len(tokens))), 4)
