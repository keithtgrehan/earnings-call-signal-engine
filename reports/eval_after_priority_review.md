# Evaluation After Priority Review

This report is safe to regenerate. It does not promote weak labels and does not mutate canonical gold labels.

## Gold Status

- current_gold_labels: `57`
- labels_needed_to_reach_100: `43`
- labels_needed_to_reach_250: `193`
- gold_growth_status_report_exists: `True`

## Metrics By Source Quality

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

## Deterministic vs ML

- deterministic_precision: `0.8399`
- deterministic_recall: `0.8326`
- deterministic_F1: `0.8276`
- ml_precision: `0.7332`
- ml_recall: `0.7328`
- ml_F1: `0.7327`
- deterministic remains canonical; ML is benchmark-only.

## Gates

- precision_above_0_5: `True`
- reached_100_labels: `False`
- retrieval_allowed: `False`
- retrieval_status: `skipped: Retrieval benchmark requires >=100 labels or --enable-retrieval-experiment.`
