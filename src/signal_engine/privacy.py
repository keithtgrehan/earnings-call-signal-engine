from __future__ import annotations

from copy import deepcopy
import hashlib
import re
from typing import Any


_EMAIL_RE = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    re.IGNORECASE,
)
_IBAN_RE = re.compile(
    r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b",
    re.IGNORECASE,
)
_CARD_RE = re.compile(r"\b(?:\d[ -]?){13,19}\d\b")
_PHONE_RE = re.compile(
    r"(?:(?<!\w)(?:\+?\d[\d(). -]{8,}\d))(?!\w)",
    re.IGNORECASE,
)
_ADDRESS_RE = re.compile(
    r"\b\d{1,5}\s+(?:[A-Za-z][A-Za-z.'-]*\s+){1,5}"
    r"(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Court|Ct)\b\.?",
    re.IGNORECASE,
)


def _hash_value(kind: str, value: str) -> str:
    normalized = value.strip().lower()
    if kind in {"phone", "card"}:
        normalized = re.sub(r"\D+", "", normalized)
    if kind == "iban":
        normalized = re.sub(r"\s+", "", normalized).upper()
    if kind == "address":
        normalized = re.sub(r"\s+", " ", normalized)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return digest[:16]


def _passes_luhn(candidate: str) -> bool:
    digits = [int(char) for char in candidate if char.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    total = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def _collect_redaction_candidates(text: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    for match in _CARD_RE.finditer(text):
        value = match.group(0)
        if not _passes_luhn(value):
            continue
        candidates.append(
            {
                "priority": 0,
                "type": "card",
                "replacement": "[CARD]",
                "value": value,
                "start": match.start(),
                "end": match.end(),
            }
        )

    for match in _IBAN_RE.finditer(text):
        candidates.append(
            {
                "priority": 1,
                "type": "iban",
                "replacement": "[IBAN]",
                "value": match.group(0),
                "start": match.start(),
                "end": match.end(),
            }
        )

    for match in _EMAIL_RE.finditer(text):
        candidates.append(
            {
                "priority": 2,
                "type": "email",
                "replacement": "[EMAIL]",
                "value": match.group(0),
                "start": match.start(),
                "end": match.end(),
            }
        )

    for match in _ADDRESS_RE.finditer(text):
        candidates.append(
            {
                "priority": 3,
                "type": "address",
                "replacement": "[ADDRESS]",
                "value": match.group(0),
                "start": match.start(),
                "end": match.end(),
            }
        )

    for match in _PHONE_RE.finditer(text):
        value = match.group(0)
        digits = re.sub(r"\D+", "", value)
        if len(digits) < 10 or len(digits) > 15:
            continue
        candidates.append(
            {
                "priority": 4,
                "type": "phone",
                "replacement": "[PHONE]",
                "value": value,
                "start": match.start(),
                "end": match.end(),
            }
        )

    filtered: list[dict[str, Any]] = []
    for candidate in sorted(
        candidates,
        key=lambda item: (item["start"], item["priority"], -(item["end"] - item["start"])),
    ):
        if any(
            not (candidate["end"] <= kept["start"] or candidate["start"] >= kept["end"])
            for kept in filtered
        ):
            continue
        filtered.append(candidate)
    return filtered


def redact_pii_text(text: str) -> dict[str, Any]:
    original_text = str(text or "")
    candidates = _collect_redaction_candidates(original_text)
    if not candidates:
        return {"text": original_text, "redactions": []}

    redacted_parts: list[str] = []
    redactions: list[dict[str, Any]] = []
    cursor = 0
    for candidate in sorted(candidates, key=lambda item: item["start"]):
        start = candidate["start"]
        end = candidate["end"]
        redacted_parts.append(original_text[cursor:start])
        redacted_parts.append(candidate["replacement"])
        redactions.append(
            {
                "type": candidate["type"],
                "original_hash": _hash_value(candidate["type"], candidate["value"]),
                "replacement": candidate["replacement"],
                "start": start,
                "end": end,
            }
        )
        cursor = end
    redacted_parts.append(original_text[cursor:])
    return {"text": "".join(redacted_parts), "redactions": redactions}


def redact_conversation(conversation: dict[str, Any]) -> dict[str, Any]:
    payload = deepcopy(conversation)
    all_redactions: list[dict[str, Any]] = []

    for field_name in ("transcript_segments", "messages"):
        raw_segments = payload.get(field_name)
        if not isinstance(raw_segments, list):
            continue
        for index, segment in enumerate(raw_segments):
            if not isinstance(segment, dict):
                continue
            for text_key in ("text", "message", "content"):
                raw_text = segment.get(text_key)
                if not isinstance(raw_text, str):
                    continue
                redacted = redact_pii_text(raw_text)
                segment[text_key] = redacted["text"]
                for item in redacted["redactions"]:
                    redaction = dict(item)
                    redaction["field_path"] = f"{field_name}[{index}].{text_key}"
                    all_redactions.append(redaction)

    return {
        "conversation": payload,
        "redactions": all_redactions,
    }


def summarize_redactions(redactions: list[dict[str, Any]]) -> dict[str, Any]:
    by_type: dict[str, int] = {}
    for item in redactions:
        kind = str(item.get("type", "unknown"))
        by_type[kind] = by_type.get(kind, 0) + 1
    return {
        "total_redactions": len(redactions),
        "by_type": by_type,
        "unique_hashes": len({item.get("original_hash") for item in redactions}),
    }


__all__ = [
    "redact_conversation",
    "redact_pii_text",
    "summarize_redactions",
]
