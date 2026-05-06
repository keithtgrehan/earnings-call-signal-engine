# Metric Jump Validation

The deterministic metric jump is promising, but it is not yet a product-quality claim.

## Source Group Counts

- `fixture`: 36
- `human_reviewed`: 12
- `imported_guidance`: 9

## Per-Label Support

- `risk_friction`: 13
- `opportunity_commitment`: 15
- `uncertainty_hedging`: 18
- `neutral`: 11

## Subset Metrics

### all

- rows: `57`
- precision: `0.8399`
- recall: `0.8326`
- F1: `0.8276`

### human_reviewed

- rows: `12`
- precision: `0.6`
- recall: `0.6375`
- F1: `0.5794`

### fixture_excluded

- rows: `21`
- precision: `0.6429`
- recall: `0.6833`
- F1: `0.646`

### imported_guidance

- rows: `9`
- precision: `0.75`
- recall: `0.75`
- F1: `0.75`

### human_reviewed_priority_packet

- rows: `0`
- rows: `0`
- precision: `n/a`
- recall: `n/a`
- F1: `n/a`

## Robustness Assessment

- The all-label improvement is large and passes the deterministic regression checks.
- Fixture rows still dominate the current label set, so the improvement must be validated on more real human-reviewed earnings-call labels.
- Human-reviewed-only support is still small; one or two labels can swing metrics materially.
- No labels are promoted by this report, and the review packet generator excludes rows already in canonical gold labels.
- Deterministic output is compared to canonical gold labels only; ML and retrieval do not alter the comparison.

## Recommendation

Treat `0.8399` precision / `0.8276` F1 as a strong regression signal, not as a robust performance claim. The next proof milestone is 100+ high-quality human-reviewed labels.
