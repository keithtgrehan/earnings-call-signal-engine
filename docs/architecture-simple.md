# Architecture Simple

Signal Engine 2.0 is a transcript-first deterministic signal extraction engine.

```text
Transcript / call text
  ↓
Normalization + segmentation
  ↓
Deterministic extraction core
  ↓
Signal registry
  ↓
Evidence-backed structured output
  ↓
Optional adapters:
  - text emotion benchmark
  - retrieval
  - long-context review
  - audio/video audit later
```

## What Is Canonical Now

- transcript input
- deterministic rules and lexicons
- evidence snippets tied to concrete turns
- structured JSON outputs used for review

## What Is Optional

- text-emotion benchmarking
- retrieval helpers
- local transformer comparisons when dependencies and cache are already available
- later audio or video sidecars

## What Is Roadmap

- production ASR
- production diarization
- audio cue extraction for escalated cases
- video cue extraction for escalated cases
- multimodal fusion with measured reviewer-lift studies

## Why Deterministic-First Matters

- outputs stay reviewable and reproducible
- reviewers can challenge individual signals instead of trusting a black box
- optional models can be benchmarked without becoming the source of truth
- the repo remains lightweight enough for CI, demos, and portfolio review
