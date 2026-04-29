# Conversation Schema

The deterministic QA and risk engine accepts JSON, JSONL, or JSON arrays with one conversation per record.

## Canonical shape

```json
{
  "conversation_id": "support_case_001",
  "messages": [
    {
      "role": "customer",
      "text": "I need help with a duplicate charge.",
      "timestamp": "2026-04-23T10:00:00Z"
    },
    {
      "role": "agent",
      "text": "I checked the charge and opened the refund.",
      "timestamp": "2026-04-23T10:01:00Z"
    }
  ]
}
```

## Required fields

- `conversation_id`: string
- `messages`: list of message objects
- `messages[].role`: `agent` or `customer`
- `messages[].text`: string

## Optional fields

- `messages[].timestamp`: string

## Deterministic parser behavior

- Whitespace is normalized.
- Consecutive messages from the same role are coalesced into one block.
- Customer messages are paired with the next agent message.
- Orphan agent messages are preserved deterministically but do not create extra output rows.
- Missing agent replies stay visible as unanswered customer turns.

## Reference-domain mapping

The same schema also covers earnings-call Q&A:

- analyst -> `customer`
- management -> `agent`

That keeps support QA as the primary product path while preserving earnings calls as a reference domain.
