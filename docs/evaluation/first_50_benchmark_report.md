# First 50 Benchmark Report

This report is a readiness template. It must not claim precision, recall, F1, uplift, significance, or production validity until metrics are computed from valid human gold labels.

## Current Gate

- gold_labels: `0`
- evaluation_gate: `insufficient_data`
- metrics_allowed: `False`
- training_gate: `skip_training`
- training_allowed: `False`
- benchmark_claims_allowed: `False`
- label_coverage_csv: `reports/label_coverage.csv`

## Label Coverage

- `neutral`: 0
- `opportunity_commitment`: 0
- `risk_friction`: 0
- `uncertainty_hedging`: 0

- missing_labels: `neutral, opportunity_commitment, risk_friction, uncertainty_hedging`
- duplicate_gold_ids: `none`
- invalid_label_rows: `none`

## Reviewed Batch Status

- accepted: `0`
- rejected: `0`
- unclear: `0`
- skipped: `0`
- unreviewed: `0`

## Claims Boundary

- Transcript-first deterministic extraction remains canonical.
- Weak labels and model suggestions are not gold labels.
- Rejected, unclear, skipped, and unreviewed rows are excluded from gold.
- Below 20 gold labels, metrics are intentionally skipped.
- Below 50 gold labels, text model training remains gated.
