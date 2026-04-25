# Label Dataset Growth Report

This report tracks reviewed-label growth without turning mined candidates into truth automatically.

- current_reviewed_label_count: `48`
- candidate_count: `321`
- accepted_candidate_count: `0`
- benchmark_training_ready: `True`
- gold_holdout_viable: `True`

## Current Class Balance

- `risk_friction`: `12`
- `opportunity_commitment`: `13`
- `uncertainty_hedging`: `12`
- `neutral`: `11`

## Gap To Milestones

- `100_labels`: `52` more reviewed labels needed
- `300_labels`: `252` more reviewed labels needed
- `1000_labels`: `952` more reviewed labels needed

## Recommendation

- Prioritize the next 20-30 reviewed rows toward the thinnest classes, starting with neutral (11), risk_friction (12), while keeping at least 20 percent of the batch neutral.

## Boundaries

- Local fixtures remain the primary training source.
- Candidate mining creates review queues only.
- Manual review is still required before promotion into the canonical label set.
