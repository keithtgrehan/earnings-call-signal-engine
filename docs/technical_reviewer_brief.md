# Technical Reviewer Brief

## One-line summary

Signal Engine is a transcript-first evaluation system that converts earnings-call transcripts into evidence-backed signal candidates, human-review packets, and benchmark reports.

## Problem

Generic AI summaries are hard to trust because they lack evidence, provenance, quality gates, and measurable evaluation.

## System architecture

- Source discovery
- Transcript intake
- Provenance capture
- Deterministic signal extraction
- Weak-label candidate generation
- Human review
- Gold-label promotion
- Evaluation loop
- ML/retrieval benchmark layers

## Why deterministic first

Deterministic extraction is easier to audit, produces stable evidence spans, and is useful before large label volume exists. It also creates a benchmarkable baseline that ML and retrieval layers can be compared against later.

## Current metrics

- Canonical gold labels: `57`
- Deterministic precision: `0.8399`
- Deterministic recall: `0.8326`
- Deterministic F1: `0.8276`
- TF-IDF + Logistic Regression precision: `0.7332`
- TF-IDF + Logistic Regression recall: `0.7328`
- TF-IDF + Logistic Regression F1: `0.7327`
- Label distribution: `risk_friction=13`, `opportunity_commitment=15`, `uncertainty_hedging=18`, `neutral=11`

These are promising early scores, not final production claims. Label volume is still small.

## What is built

- Intake pipeline
- Source discovery
- Manual source workflow
- Provenance files
- Review packet generation
- Gold-label promotion workflow
- Evaluation reports
- Offline portfolio demo
- Gated retrieval benchmark

## What is not claimed

- No trading automation
- No investment advice
- No production ML model
- No statistical significance claim
- No automated label promotion

## Why it matters commercially

The reusable pattern is messy business communication to structured evidence to human-review workflow to measurable quality reporting.

## Next scale target

- 100 calls
- 500-1,000 reviewed labels
- Stronger ML/retrieval benchmark
- Source-quality breakdown
- Error analysis by label class

## How to review quickly

Commands:

```bash
make portfolio-demo
pytest -q
ruff check .
```

Files:

- `PORTFOLIO_README.md`
- `docs/portfolio_architecture.md`
- `docs/evaluation_strategy.md`
- `reports/demo/portfolio_demo_report.md`
- `reports/evaluation_status.md`
