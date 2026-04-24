from __future__ import annotations

import json

from signal_engine.privacy import redact_conversation, redact_pii_text, summarize_redactions


def test_redact_pii_text_masks_sensitive_patterns_without_storing_raw_values() -> None:
    text = (
        "Email me at ops@northwind.example, call +1 (415) 555-0114, "
        "bill 4111 1111 1111 1111, use DE89370400440532013000, "
        "and ship to 123 Market Street."
    )
    result = redact_pii_text(text)

    assert "[EMAIL]" in result["text"]
    assert "[PHONE]" in result["text"]
    assert "[CARD]" in result["text"]
    assert "[IBAN]" in result["text"]
    assert "[ADDRESS]" in result["text"]

    serialized = json.dumps(result["redactions"], ensure_ascii=False)
    assert "ops@northwind.example" not in serialized
    assert "415" not in serialized
    assert "4111 1111 1111 1111" not in serialized
    assert "DE89370400440532013000" not in serialized
    assert "123 Market Street" not in serialized


def test_redact_conversation_preserves_structure_and_summarizes_redactions() -> None:
    conversation = {
        "conversation_id": "privacy_case",
        "messages": [
            {
                "role": "customer",
                "text": "Please call me at 415-555-0114 or email me at finance@northwind.example.",
            },
            {
                "role": "agent",
                "text": "We still have the card 4111 1111 1111 1111 on file at 123 Market Street.",
            },
        ],
    }

    result = redact_conversation(conversation)
    redacted = result["conversation"]
    summary = summarize_redactions(result["redactions"])

    assert redacted["conversation_id"] == conversation["conversation_id"]
    assert len(redacted["messages"]) == 2
    assert "[PHONE]" in redacted["messages"][0]["text"]
    assert "[EMAIL]" in redacted["messages"][0]["text"]
    assert "[CARD]" in redacted["messages"][1]["text"]
    assert "[ADDRESS]" in redacted["messages"][1]["text"]
    assert summary["total_redactions"] == 4
    assert summary["by_type"]["email"] == 1
    assert all("field_path" in item for item in result["redactions"])
