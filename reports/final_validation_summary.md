# Final Validation Summary

## Before Metrics

- precision: `0.3205`
- recall: `0.4499`
- F1: `0.3743`

## After Metrics

- precision: `0.8399`
- recall: `0.8326`
- F1: `0.8276`

## Deltas

- precision_delta: `0.5194`
- recall_delta: `0.3827`
- F1_delta: `0.4533`

## Accepted Refinements

- Conditional suppression for generic opportunity/process triggers.
- Neutral-status suppression for generic renewal/legal/open/process triggers.
- Guidance/outlook detection for raised, flat, down, range, and expected-revenue language.
- Explainability fields added while preserving `predict_deterministic_signal_family()` compatibility.

## Rejected Refinements

- No deterministic architecture rewrite.
- No synthetic labels or canonical gold-label mutation.
- No ML or retrieval override of deterministic outputs.
- No production, alpha, or statistical claims.

## Source-Quality Findings

- Fixture rows remain useful for regression checks but cannot support product claims.
- Imported guidance rows add finance-specific coverage and require manual provenance review.
- More high-quality human-reviewed labels are needed before retrieval or ML product claims.

## Deterministic vs ML Outcome

- ML benchmark report exists: `True`
- TF-IDF/logistic regression is benchmark-only and currently useful for disagreement analysis.
- Deterministic output remains canonical because it is more explainable and now stronger on this benchmark.

## Retrieval Benchmark Result

- retrieval benchmark report exists: `True`
- Retrieval remains gated by default until 100+ labels or explicit experiment mode.
- Retrieval evidence objects are generated for review/search benchmarking only.

## Remaining Weaknesses

- Opportunity versus uncertainty remains the highest-risk confusion family.
- Neutral operational status can still resemble commitment when language is terse.
- Current metrics are from 57 mixed-provenance labels and may move as the real label set grows.

## Next Highest-Leverage Improvements

- Review the next 50 prioritized examples.
- Add source-quality metadata to every future imported label.
- Expand real transcript coverage before enabling retrieval experiments by default.
