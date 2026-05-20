# Signal Engine 2.0

## One-line summary

A transcript-first evaluation engine that turns earnings-call transcripts into evidence-backed signals, human-review workflows, and benchmark reports.

## Why I built it

Generic AI summaries are hard to trust when the source material is long, messy, and commercially important. Business users need evidence, provenance, and repeatable review before they can rely on extracted signals. The goal of this repo is to make signal extraction measurable, auditable, and useful without pretending that a summary or model score is enough.

## What works now

- transcript intake
- source discovery
- provenance tracking
- deterministic signal extraction
- weak-label candidate generation
- human review packets
- gold-label promotion workflow
- evaluation reports
- TF-IDF/logistic-regression benchmark
- retrieval benchmark scaffold/gated workflow
- one-command demo

## Demo flow

1. Ingest transcript.
2. Preserve source/provenance.
3. Extract deterministic signal candidates.
4. Generate review packet.
5. Human accepts, rejects, or corrects candidates.
6. Promote accepted labels.
7. Rerun benchmark/evaluation.
8. Produce stakeholder-readable reports.

## Current status

| Capability | Status |
|---|---|
| Transcript intake | Built |
| Source discovery | Built |
| Provenance tracking | Built |
| Deterministic extraction | Built |
| Human review workflow | Built |
| Gold-label promotion | Built |
| Evaluation loop | Built |
| ML baseline | Built, early |
| Retrieval benchmark | Scaffolded/gated |
| 100-call corpus | In progress |
| Production deployment | Not claimed |

## Current metrics

Latest committed reports show:

- deterministic baseline on 57 gold labels: precision `0.8399`, recall `0.8326`, F1 `0.8276`
- human-reviewed-only subset: precision `0.6`, recall `0.6375`, F1 `0.5794` on 12 rows
- fixture-excluded subset: precision `0.6429`, recall `0.6833`, F1 `0.646` on 21 rows
- TF-IDF/logistic-regression benchmark: precision `0.7332`, recall `0.7328`, F1 `0.7327`
- retrieval status: skipped/gated until at least 100 labels or explicit retrieval experiment mode

These are small-benchmark workflow metrics. They are useful for tracking evaluation quality, not for statistical or production-performance claims.

## Commercial relevance

This repo demonstrates a reusable pattern for evidence-backed AI workflows: preserve provenance, produce reviewable outputs, measure quality against reviewed labels, keep humans in the governance loop, and package results into stakeholder-readable reports. That pattern is valuable when teams need practical AI support without losing trust, auditability, or product discipline.

## What this does not claim

- no live trading
- no automated investment advice
- no unsupported alpha claims
- no production ML claim
- no statistical-significance claim yet

## Run the portfolio demo

```bash
make portfolio-demo
```

The demo uses committed reports/fixtures only. It does not download sources, call external APIs, or create new labels.
