# Domain Schemas

Signal Engine 2.0 uses one transcript-first normalization layer with domain-specific role semantics on top.

## Common Record Shape

All domains normalize into the same core record:

```json
{
  "conversation_id": "conv_001",
  "participants": [
    {
      "participant_id": "customer_1",
      "name": "Jordan",
      "role": "customer",
      "organization": "ExampleCo"
    }
  ],
  "transcript_segments": [
    {
      "message_index": 0,
      "speaker_id": "customer_1",
      "role": "customer",
      "text": "We still need a refund date.",
      "timestamp_start": "00:00:03",
      "timestamp_end": "00:00:11"
    }
  ],
  "audio_metadata": {
    "sample_rate_hz": 16000
  },
  "video_metadata": {
    "source_fps": 30
  },
  "source": {
    "source_type": "crm_export",
    "source_path": "local/export.json",
    "notes": "Synthetic example"
  }
}
```

Required canonical fields:

- `conversation_id` or `call_id`
- `participants`
- `transcript_segments` or `messages`
- `source` or `provenance`

Optional fields:

- timestamps
- audio metadata
- video metadata
- source path and notes

## Support Conversation

Use when a customer and an agent exchange support messages.

Recommended roles:

- `customer`
- `agent`

Focus fields:

- `conversation_id`
- participants with customer and agent roles
- ordered message turns or transcript segments
- optional timestamps for escalation timing
- source or provenance for QA traceability

## Sales Call

Use when a buyer/prospect interacts with a seller or AE.

Recommended roles:

- `buyer`
- `rep`

Focus fields:

- `conversation_id` or `call_id`
- participants with buyer and seller role labels
- transcript segments with message order preserved
- optional timestamps for objection timing
- optional audio/video metadata for future review layers
- source or provenance for CRM or call-recording lineage

## Account Management Call

Use when a customer interacts with an account manager or customer success manager.

Recommended roles:

- `customer`
- `account_manager`

Focus fields:

- `conversation_id`
- participants covering customer and account-team speakers
- transcript segments capturing renewal, risk, and commitment language
- optional timestamps for issue aging and next-step commitments
- optional audio/video metadata if the call is recorded
- source or provenance for account-review traceability

## Earnings Call

Use when management responds to analysts or investors on an earnings call.

Recommended roles:

- `analyst`
- `executive`
- `operator` as optional neutral role

Focus fields:

- `call_id` or `conversation_id`
- participants for analysts, executives, and operator
- transcript segments preserving question and answer order
- optional timestamps aligned to transcript sections or audio/video
- optional audio/video metadata for later multimodal review
- source or provenance for transcript origin and auditability

## Output Schema

All domains emit the same analysis envelope:

```json
{
  "schema_version": "signal_engine_2.0",
  "domain": "support",
  "conversation_id": "conv_001",
  "scores": {
    "directness_score": 0.21
  },
  "risk_flags": [
    "support_deflection"
  ],
  "opportunity_flags": [],
  "evidence": [
    {
      "signal_name": "deflection",
      "message_index": 1,
      "matched_text": "Another team handles refunds...",
      "reason": "Support deflection language detected."
    }
  ],
  "metadata": {
    "deterministic": true,
    "external_api_required": false
  }
}
```

Evidence object fields:

- `signal_name`
- `message_index`
- `matched_text`
- `reason`
