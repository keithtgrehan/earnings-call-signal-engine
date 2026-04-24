# NLP Research Plan

## Goal

Start a serious but bounded NLP workstream that supports Signal Engine 2.0 without displacing the transcript-first deterministic core.

## Principles

- deterministic transcript extraction remains canonical
- models are benchmark tools, not product truth
- use primary sources where possible
- prefer openly documented metadata over silent downloads
- do not vendor restricted corpora or model artifacts by default

## Selection Criteria

- directly relevant to transcript review, uncertainty, friction, guidance language, or reviewer usefulness
- realistic to document and benchmark without heavy infrastructure
- useful for support, sales, account management, or earnings-call review
- compatible with offline-safe manifests and lightweight CI

## Included Source Types

- papers
- datasets
- benchmarks
- libraries

## Deliberate Scope Boundaries

- no exhaustive literature review claim
- no attempt to collect every finance or emotion paper
- no download of large corpora by default
- no model training claim unless the local data supports it honestly

## First Benchmark Task

Train a small text-only `signal_family` baseline using weak labels derived from existing deterministic rules.

Labels:

- `risk_friction`
- `opportunity_commitment`
- `uncertainty_hedging`
- `neutral`

## Why Weak Labels First

- reuses the current deterministic investment
- keeps the labeling logic auditable
- exposes where the local corpus is too small instead of hiding it
- gives the repo a real modeling workstream without forcing heavy dependencies

## Expected Near-Term Outcome

- an offline-safe research manifest in JSON and Markdown
- a reproducible training script
- either a small baseline result or an explicit insufficient-data report
- a clearer map of what additional labeled data would actually unlock
