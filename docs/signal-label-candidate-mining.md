# Signal Label Candidate Mining

This workflow mines candidate snippets from committed local fixtures, demo assets, and generated outputs.
It is a review-queue builder, not an automatic source of truth.

- candidate_count: `321`

## Suggested Label Mix

- `risk_friction`: `106`
- `opportunity_commitment`: `45`
- `uncertainty_hedging`: `4`
- `neutral`: `166`

## Boundaries

- Local project fixtures remain the primary training source.
- Candidate rows are only suggestions until a reviewer fills `reviewer_label` and marks `accepted`.
- Neutral candidates are intentionally included to avoid a purely issue-heavy queue.
