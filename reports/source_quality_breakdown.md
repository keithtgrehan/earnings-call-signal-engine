# Source Quality Breakdown

Canonical gold labels are not modified by source-quality filtering.

## Counts By Source Group

- `fixture`: 36
- `human_reviewed`: 12
- `imported_guidance`: 9

## Counts By Quality

- `high`: 12
- `low`: 36
- `medium`: 9

## Label Counts By Source

- `fixture` / `neutral`: 10
- `fixture` / `opportunity_commitment`: 11
- `fixture` / `risk_friction`: 7
- `fixture` / `uncertainty_hedging`: 8
- `human_reviewed` / `neutral`: 1
- `human_reviewed` / `opportunity_commitment`: 2
- `human_reviewed` / `risk_friction`: 5
- `human_reviewed` / `uncertainty_hedging`: 4
- `imported_guidance` / `opportunity_commitment`: 2
- `imported_guidance` / `risk_friction`: 1
- `imported_guidance` / `uncertainty_hedging`: 6

## Interpretation

- `fixture` rows are useful for regression safety but can make metrics look cleaner or stranger than real transcripts.
- `imported_guidance` rows are valuable but conservatively mapped and should be reviewed before strong product claims.
- `human_reviewed` rows are the best current quality tier, though the count remains small.
