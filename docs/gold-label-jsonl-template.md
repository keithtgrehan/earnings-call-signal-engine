# Gold Label JSONL Template

Each accepted human label should be one JSON object per line:

```json
{"case_id":"CASE_ID","evidence_text":"EXACT_TRANSCRIPT_QUOTE","label":"risk_friction","reason":"Short human reason.","confidence":"high"}
```

Allowed labels:

- `risk_friction`
- `opportunity_commitment`
- `uncertainty_hedging`
- `neutral`

Confidence rules:

- `high` = obvious, direct evidence
- `medium` = reasonable but context-dependent
- `low` = uncertain, should usually not enter gold labels

Do not copy weak labels into gold labels without human review. Use exact transcript quotes only.
