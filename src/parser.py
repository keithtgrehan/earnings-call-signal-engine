from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

VALID_ROLES = {"agent", "customer"}
_WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(text: Any) -> str:
    if text is None:
        return ""
    return _WHITESPACE_RE.sub(" ", str(text)).strip()


def _coerce_role(value: Any) -> str:
    role = normalize_text(value).lower()
    if role not in VALID_ROLES:
        raise ValueError(f"Unsupported role: {value!r}. Expected one of {sorted(VALID_ROLES)}.")
    return role


def _normalize_message(message: dict[str, Any]) -> dict[str, str]:
    normalized: dict[str, str] = {
        "role": _coerce_role(message.get("role")),
        "text": normalize_text(message.get("text")),
    }
    timestamp = normalize_text(message.get("timestamp"))
    if timestamp:
        normalized["timestamp"] = timestamp
    return normalized


def _coalesce_messages(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    coalesced: list[dict[str, str]] = []
    for message in messages:
        if not message["text"]:
            continue
        if coalesced and coalesced[-1]["role"] == message["role"]:
            coalesced[-1]["text"] = f"{coalesced[-1]['text']} {message['text']}".strip()
            if "timestamp" not in coalesced[-1] and "timestamp" in message:
                coalesced[-1]["timestamp"] = message["timestamp"]
            continue
        coalesced.append(dict(message))
    return coalesced


def pair_customer_agent_messages(messages: list[dict[str, str]]) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    current_customer: dict[str, str] | None = None

    for message in messages:
        if message["role"] == "customer":
            if current_customer is not None:
                pairs.append({"customer": current_customer, "agent": None})
            current_customer = message
            continue

        if current_customer is None:
            pairs.append({"customer": None, "agent": message})
            continue

        pairs.append({"customer": current_customer, "agent": message})
        current_customer = None

    if current_customer is not None:
        pairs.append({"customer": current_customer, "agent": None})

    return pairs


def parse_conversation(record: dict[str, Any], *, index: int = 0) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("Conversation record must be a JSON object.")

    conversation_id = normalize_text(record.get("conversation_id")) or f"conversation_{index:04d}"
    raw_messages = record.get("messages") or []
    if not isinstance(raw_messages, list):
        raise ValueError(f"Conversation {conversation_id} has non-list messages.")

    messages = _coalesce_messages(
        [_normalize_message(message) for message in raw_messages if isinstance(message, dict)]
    )
    pairs = pair_customer_agent_messages(messages)
    orphan_agent_messages = sum(
        1 for pair in pairs if pair["customer"] is None and pair["agent"] is not None
    )
    unanswered_customer_messages = sum(
        1 for pair in pairs if pair["customer"] is not None and pair["agent"] is None
    )

    return {
        "conversation_id": conversation_id,
        "messages": messages,
        "pairs": pairs,
        "message_count": len(messages),
        "pair_count": sum(1 for pair in pairs if pair["customer"] is not None),
        "orphan_agent_messages": orphan_agent_messages,
        "unanswered_customer_messages": unanswered_customer_messages,
    }


def _load_json(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("messages"), list):
        return [payload]
    if isinstance(payload, dict) and isinstance(payload.get("conversations"), list):
        return [item for item in payload["conversations"] if isinstance(item, dict)]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    raise ValueError(f"Unsupported JSON structure in {path}.")


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        item = json.loads(stripped)
        if not isinstance(item, dict):
            raise ValueError(f"Line {line_number} in {path} is not a JSON object.")
        records.append(item)
    return records


def load_conversations(path: str | Path) -> list[dict[str, Any]]:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix == ".json":
        raw_records = _load_json(file_path)
    elif suffix == ".jsonl":
        raw_records = _load_jsonl(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix}. Use JSON or JSONL.")

    return [parse_conversation(record, index=index) for index, record in enumerate(raw_records, start=1)]
