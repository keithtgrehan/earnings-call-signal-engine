# Support QA MVP

## What it does

This repo now centers on a deterministic, explainable conversation signal engine for support QA and risk detection.

Given a JSON or JSONL conversation, it:

- validates a simple agent/customer schema
- pairs customer prompts with the next agent reply
- extracts deterministic lexical and Q&A behavior features
- emits one structured output row per conversation
- raises explainable risk flags for frustration, deflection, low directness, and inconsistent messaging

## Why it matters

Support teams need audit-friendly QA signals without adding model drift, hidden prompts, or external dependencies.

This MVP is designed for:

- offline batch scoring
- CSV or JSON export pipelines
- quality review baselines
- escalation triage inputs

## What it does not do

- no LLM scoring
- no external APIs
- no UI or dashboard
- no conversation summaries
- no decisioning hidden behind embeddings

## Reference domain

The repo still preserves earnings-call workflow and datasets as a proof layer for messy long-form Q&A, but customer support QA is now the primary framing.
