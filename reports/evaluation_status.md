# Evaluation Status

Insufficient gold labels for evaluation

```json
{
  "gold_labels": 0,
  "valid_gold_rows_with_text": 0,
  "label_counts": {
    "risk_friction": 0,
    "opportunity_commitment": 0,
    "uncertainty_hedging": 0,
    "neutral": 0
  },
  "missing_labels": [
    "risk_friction",
    "opportunity_commitment",
    "uncertainty_hedging",
    "neutral"
  ],
  "evaluation_gate": "insufficient_data",
  "metrics_allowed": false,
  "training_gate": "skip_training",
  "training_allowed": false,
  "embeddings_allowed": false,
  "dataset_benchmarks_allowed": false,
  "benchmark_claims_allowed": false,
  "canonical_truth": "deterministic_system",
  "enforcement": {
    "no_synthetic_labels": true,
    "no_weak_label_auto_promotion": true,
    "no_metrics_without_valid_gold": true,
    "no_statistical_claims": true,
    "no_silent_dataset_usage": true,
    "embeddings_cannot_override_deterministic_outputs": true
  },
  "threshold": 20,
  "metrics_computed": false,
  "message": "Insufficient gold labels for evaluation"
}
```
