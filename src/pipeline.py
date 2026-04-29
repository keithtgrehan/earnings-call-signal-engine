from __future__ import annotations

from pathlib import Path
from typing import Any

from features import (
    agent_message_count,
    compute_feature_set,
    customer_negative_ratio,
)
from parser import load_conversations, parse_conversation


def build_risk_flags(parsed_conversation: dict[str, Any], features: dict[str, float]) -> list[str]:
    flags: list[str] = []
    if customer_negative_ratio(parsed_conversation) > 0.2:
        flags.append("customer_frustration")
    if features["qa_deflection_rate"] > 0.3:
        flags.append("agent_deflection")
    if features["directness_score"] < 0.4:
        flags.append("low_directness")
    if agent_message_count(parsed_conversation) >= 2 and features["consistency_score"] < 0.5:
        flags.append("inconsistent_messaging")
    return flags


def analyze_parsed_conversation(parsed_conversation: dict[str, Any]) -> dict[str, Any]:
    features = compute_feature_set(parsed_conversation)
    return {
        "conversation_id": parsed_conversation["conversation_id"],
        "qa_score": features["qa_score"],
        "directness_score": features["directness_score"],
        "consistency_score": features["consistency_score"],
        "negative_language_ratio": features["negative_language_ratio"],
        "positive_language_ratio": features["positive_language_ratio"],
        "hedging_ratio": features["hedging_ratio"],
        "verbosity_ratio": features["verbosity_ratio"],
        "qa_deflection_rate": features["qa_deflection_rate"],
        "risk_flags": build_risk_flags(parsed_conversation, features),
    }


def analyze_conversation_record(record: dict[str, Any], *, index: int = 1) -> dict[str, Any]:
    parsed = parse_conversation(record, index=index)
    return analyze_parsed_conversation(parsed)


def analyze_file(path: str | Path) -> list[dict[str, Any]]:
    parsed_conversations = load_conversations(path)
    return [analyze_parsed_conversation(parsed) for parsed in parsed_conversations]
