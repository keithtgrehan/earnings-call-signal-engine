# Agent 1 False-Positive Guardrails

The deterministic pilot favors precision and reviewability over broad recall.

Suppressed or downgraded buckets:

- `boilerplate_safe_harbor`
- `boilerplate_non_gaap`
- `operator_text`
- `transcript_disclaimer`
- `generic_optimism`
- `historical_only`
- `normal_analyst_question`
- `analyst_only_unpaired`
- `duplicate_repeated_text`
- `metric_mismatch`
- `period_mismatch`
- `speaker_role_unknown`
- `source_unregistered`
- `provenance_missing`

Guidance revision candidates need a management speaker, guidance cue, metric or outlook, period, and prior/current comparator for full revision proof. Missing comparator stays a candidate with `prior_missing`; it is not a confirmed guidance revision.

Analyst pressure and answer-shift candidates require Q&A context. Unpaired analyst questions remain low-confidence candidates.
