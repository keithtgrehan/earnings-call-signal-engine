from __future__ import annotations

from features import compute_feature_set
from parser import parse_conversation
from pipeline import analyze_conversation_record


def _assert_feature_ranges(feature_set: dict[str, float]) -> None:
    for value in feature_set.values():
        assert 0.0 <= value <= 1.0


def test_feature_ranges_on_direct_response() -> None:
    conversation = {
        "conversation_id": "range_case",
        "messages": [
            {"role": "customer", "text": "Why was my order delayed?"},
            {"role": "agent", "text": "I checked the shipment. The delay happened because the address was incomplete and you can update it now."},
        ],
    }
    parsed = parse_conversation(conversation)
    feature_set = compute_feature_set(parsed)
    _assert_feature_ranges(feature_set)


def test_feature_engine_is_deterministic() -> None:
    conversation = {
        "conversation_id": "deterministic_case",
        "messages": [
            {"role": "customer", "text": "Can you help with the refund issue?"},
            {"role": "agent", "text": "Yes. I can confirm the refund was approved and it will post tomorrow."},
        ],
    }
    first = analyze_conversation_record(conversation)
    second = analyze_conversation_record(conversation)
    assert first == second


def test_empty_messages_edge_case() -> None:
    result = analyze_conversation_record({"conversation_id": "empty_case", "messages": []})
    assert result["conversation_id"] == "empty_case"
    assert 0.0 <= result["qa_score"] <= 1.0
    assert "low_directness" in result["risk_flags"]


def test_single_message_edge_case() -> None:
    result = analyze_conversation_record(
        {
            "conversation_id": "single_case",
            "messages": [{"role": "customer", "text": "Hello?"}],
        }
    )
    assert 0.0 <= result["directness_score"] <= 1.0
    assert result["qa_deflection_rate"] == 1.0


def test_no_agent_reply_edge_case() -> None:
    result = analyze_conversation_record(
        {
            "conversation_id": "no_reply_case",
            "messages": [
                {"role": "customer", "text": "Why is my invoice wrong?"},
                {"role": "customer", "text": "I still need an answer."},
            ],
        }
    )
    assert result["qa_deflection_rate"] == 1.0
    assert "agent_deflection" in result["risk_flags"]
