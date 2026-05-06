# Baseline Snapshot

- branch: `codex/nlp-assets-tooling-registry`
- commit: `4580fdb618b3cab6ca8ca3c94cc679ddac3eceb3`
- gold_labels: `57`
- label_counts: `{'risk_friction': 13, 'opportunity_commitment': 15, 'uncertainty_hedging': 18, 'neutral': 11}`

## Starting Metrics

- precision: `0.3205`
- recall: `0.4499`
- F1: `0.3743`

## Current Metrics After Accepted Rule Refinement

- precision: `0.8399`
- recall: `0.8326`
- F1: `0.8276`

## Experiment Outputs

- `reports/experiment_results/local_ml_baseline.md`
- `reports/experiment_results/lexicon_comparison.md`
- `reports/experiment_results/dataset_comparison.md`

## Retrieval Status

- retrieval_report_exists: `True`
- default gate: requires `>=100` labels or explicit retrieval experiment flag

## Gating State

- evaluation_readiness: `True`
- local_ml: `allowed` because gold labels >= 50
- embeddings: `gated` because gold labels < 100
