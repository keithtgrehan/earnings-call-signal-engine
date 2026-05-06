# Signal Engine Case Study

Signal Engine demonstrates a transcript-first path from earnings-call evidence spans to measurable deterministic evaluation.

## Problem

Earnings calls mix prepared remarks, analyst pressure, guidance language, operational status, and generic optimism. The useful product problem is making evidence, labels, and evaluation gates visible enough for a human reviewer to trust.

## Approach

The repo keeps deterministic signal extraction canonical. Around that core it adds human-reviewed gold labels, source-quality filtering, local ML comparison, and gated retrieval benchmarks.

## Current Result

- Gold labels: `57`
- Deterministic precision: `0.8399`
- Deterministic recall: `0.8326`
- Deterministic F1: `0.8276`
- Local TF-IDF/Logistic Regression benchmark F1: `0.7327`
- Priority review packet: `data/labeling/priority_review_packet.csv`

## Next Proof Milestone

The metric jump is promising but still comes from a small mixed-provenance label set. The next milestone is 100+ high-quality human-reviewed earnings-call labels, starting with the Priority 1 review packet.

## Non-Claims

This is not a trading system, stock predictor, alpha engine, production ML model, or statistically significant benchmark.
