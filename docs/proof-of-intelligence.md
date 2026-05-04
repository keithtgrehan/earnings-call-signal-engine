# Proof of Intelligence: Transcript-First Earnings Call Signal Engine

## Problem

Earnings calls are long, noisy, and difficult to compare across companies. A useful system needs to preserve transcript evidence, identify signal-bearing moments, and stay conservative about what it can prove.

## What Was Built

Built a transcript-first earnings-call analysis system that converts raw public earnings-call transcripts into structured, evidence-backed signal outputs, with deterministic extraction, audit trails, raw-text hashing, human-reviewed gold labels, and conservative evaluation reporting.

## Current Corpus

- Active cases: 31
- Analyzed successfully: 31/31
- Quarantined cases: 0
- Duplicate transcripts: 0
- Raw mutation verification: passed
- Excluded-case reference check: passed

## Pipeline Architecture

1. Raw transcript intake preserves canonical `raw/transcript.txt`.
2. Non-destructive cleaning writes derived text only.
3. Section splitting separates prepared remarks, Q&A, and unknown text.
4. Speaker extraction creates structured speaker turns.
5. Deterministic rules extract weak labels, guidance candidates, and signal evidence.
6. Human-reviewed gold labels validate a starter benchmark layer.
7. Conservative reports compare weak labels with gold labels using span overlap.

## Signal Taxonomy

- Guidance / performance signal
- Analyst pressure / friction signal
- Uncertainty / hedge signal
- Management commitment / opportunity signal
- Neutral / no-signal evidence

## Deterministic vs. Human-Reviewed

Deterministic outputs are the baseline and source of reproducible system behavior. Gold labels are human-reviewed benchmark evidence and are never generated automatically from weak labels.

## Current Proof Points

- 31 active transcript cases.
- 31 cases analyzed successfully.
- 0 quarantined cases.
- 0 duplicate transcripts.
- Raw transcript hash verification passed.
- Excluded-case reference check passed.
- Gold-label validation tooling supports 5 starter files and reports valid label counts when human labels exist.
- Weak-vs-gold evaluation supports exact and overlap matching without claiming statistical significance.

## Evaluation Status

This is an early benchmark layer. It can show whether deterministic weak labels overlap human-reviewed evidence spans, identify missed gold labels, identify extra weak labels, and surface type mismatches.

It does not prove investment accuracy, stock prediction, alpha, trading edge, statistically significant uplift, or production ML performance.

## What This Proves

- The corpus pipeline is reproducible and transcript-first.
- Analysis outputs are evidence-backed and auditable.
- Raw transcripts are protected from mutation.
- A human-label benchmark workflow exists.
- The project can report conservative weak-vs-gold comparison rows once human labels are present.

## What Is Not Proven

- No alpha or trading edge is proven.
- No investment advice is provided.
- No statistically significant model-performance claim is made.
- No production ML system is claimed.

## Next Benchmark Step

Expand each starter case from 5 labels to 15-25 human-reviewed labels, with more neutral labels and more analyst-pressure examples. Then rerun validation, distribution checks, and weak-vs-gold overlap evaluation.

## Why This Is Stronger Than Generic Transcript Summarization

Generic summarization compresses a call into prose. This system keeps the transcript canonical, attaches structured signal types to exact evidence spans, preserves reproducible deterministic rules, validates human labels, and reports conservative evaluation artifacts.
