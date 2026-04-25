# Transcript Baseline Benchmark

This is an early labeled benchmark, not statistical proof.
The classifier is a research benchmark only.
Deterministic rules remain canonical unless the benchmark proves otherwise.

## Dataset

- path: `data/nlp_research/human_reviewed_signal_labels.jsonl`
- dataset_size: `48`

| label | support |
| --- | --- |
| risk_friction | 12 |
| opportunity_commitment | 13 |
| uncertainty_hedging | 12 |
| neutral | 11 |

## Evaluation Setup

- split_strategy: `train_test_split`
- classifier_model: `tfidf_logistic_regression`
- canonical_system: `deterministic_rules`
- evaluation_set_size: `16`

## Headline Results

| system | accuracy | macro_f1 |
| --- | --- | --- |
| deterministic_rules | 0.5000 | 0.4048 |
| tfidf_logistic_regression | 0.5000 | 0.5000 |

## Per-Class Metrics: Deterministic Rules

| label | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| risk_friction | 0.5000 | 1.0000 | 0.6667 | 4 |
| opportunity_commitment | 0.6000 | 0.7500 | 0.6667 | 4 |
| uncertainty_hedging | 0.0000 | 0.0000 | 0.0000 | 4 |
| neutral | 0.3333 | 0.2500 | 0.2857 | 4 |

## Per-Class Metrics: Classifier

| label | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| risk_friction | 0.5000 | 0.2500 | 0.3333 | 4 |
| opportunity_commitment | 0.3333 | 0.5000 | 0.4000 | 4 |
| uncertainty_hedging | 0.5000 | 0.7500 | 0.6000 | 4 |
| neutral | 1.0000 | 0.5000 | 0.6667 | 4 |

## Confusion Summary: Deterministic Rules

| true \ predicted | risk_friction | opportunity_commitment | uncertainty_hedging | neutral |
| --- | --- | --- | --- | --- |
| risk_friction | 4 | 0 | 0 | 0 |
| opportunity_commitment | 0 | 3 | 0 | 1 |
| uncertainty_hedging | 2 | 1 | 0 | 1 |
| neutral | 2 | 1 | 0 | 1 |

## Confusion Summary: Classifier

| true \ predicted | risk_friction | opportunity_commitment | uncertainty_hedging | neutral |
| --- | --- | --- | --- | --- |
| risk_friction | 1 | 3 | 0 | 0 |
| opportunity_commitment | 0 | 2 | 2 | 0 |
| uncertainty_hedging | 0 | 1 | 3 | 0 |
| neutral | 1 | 0 | 1 | 2 |

## Limitations

- The labeled set is small, hand-seeded, and drawn from committed local fixtures only.
- Many seeded labels were chosen with help from deterministic lexicons, so this benchmark is not independent proof of model superiority.
- The benchmark is useful for reviewer-facing proof, error inspection, and future iteration, not for claims of production readiness or statistical significance.
