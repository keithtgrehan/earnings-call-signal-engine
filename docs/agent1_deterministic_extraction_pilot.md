# Agent 1 Deterministic Extraction Pilot

Agent 1 generates reviewable transcript-backed candidates from manually registered, rights-cleared local transcript paths. It does not download sources, write canonical gold labels, train models, or override deterministic outputs.

Target candidate labels:

- `guidance_revision`
- `analyst_pressure`
- `management_hedging`
- `uncertainty`
- `reassurance`
- `answer_shift`
- `neutral/no_signal`

Every candidate must preserve:

- `case_id`
- source path reference and `sha256` hash
- section and speaker metadata
- span reference
- rule id/version
- provenance hash
- contamination flags
- `gold_status=not_gold`
- `review_status=pending_human_review`

If no registered manual-local transcripts exist, the pilot reports `NOT_READY` and points reviewers to manual-local registration.
