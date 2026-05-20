# Product One Pager

Signal Engine is an evidence-backed earnings-call review and signal detection workflow for analysts, investor relations, and research teams.

## What It Does

- Turns transcripts into reviewable evidence spans.
- Classifies spans into `risk_friction`, `opportunity_commitment`, `uncertainty_hedging`, and `neutral`.
- Keeps deterministic transcript-first rules as the canonical output.
- Measures performance against canonical gold labels.
- Provides a human review packet for growing high-quality labels from 57 toward 100+.

## Current Proof State

- Gold labels: `57`
- Deterministic metrics: precision `0.8399`, recall `0.8326`, F1 `0.8276`
- TF-IDF + Logistic Regression benchmark: precision `0.7332`, recall `0.7328`, F1 `0.7327`
- Retrieval benchmark: operational but gated below 100 labels.

## What Makes It Credible

- Evidence spans are inspectable.
- Gold-label promotion requires explicit human `accept` decisions.
- Source-quality reports separate fixture, imported guidance, and human-reviewed subsets.
- ML and retrieval are benchmark-only; they cannot override deterministic outputs.

## What It Is Not

Signal Engine is not a stock predictor, trading bot, alpha engine, production ML system, or statistically validated market model.
