# Project Goals And Scope

## Revised Product Objective

Build a multimodal communication intelligence engine that detects business signals, sentiment, emotion proxies, and intent across long-form business communication. The system should be measurable, reproducible, provenance-preserving, and conservative about claims.

Text is the anchor. Audio and video augment text at the segment level when media is available and aligned. The system should make uncertainty and disagreement visible instead of hiding them.

## Target Domains

- Earnings calls / finance.
- B2B sales.
- Account management / customer success.
- Customer support.
- HR / internal communication.

## Modalities

- Text: transcript, speaker turns, evidence spans, deterministic rules, weak labels, baseline classifiers, transformer candidates.
- Audio: ASR alignment, pauses, speech rate, pitch, energy, jitter/shimmer where supported, hesitation and confidence proxies.
- Video: flagged-segment frame analysis, facial emotion candidates, head pose, gaze/eye movement proxies, motion intensity, engagement and stress proxies.
- Multimodal: text embeddings plus bounded audio/video features, fused with text as anchor.

## Label Families

Business signals:

- `risk_friction`
- `opportunity_commitment`
- `uncertainty_hedging`
- `neutral`

Sentiment:

- `positive`
- `negative`
- `neutral`

Emotion/proxy labels:

- `stress`
- `confidence`
- `uncertainty`
- `frustration`
- `engagement`
- `calm/neutral`

Intent:

- `question`
- `objection`
- `commitment`
- `escalation`
- `reassurance`
- `deflection`

## Core Principles

- Text is the anchor.
- Audio/video augment text at segment level.
- No unsupported emotion certainty claims.
- Emotion detection is probabilistic and evidence-backed.
- Human review is minimized, but human gold labels remain the benchmark source.
- Weak labels and LLM triage are not gold.
- All outputs preserve provenance.
- No live trading or alpha claims.
- No fake SOTA claims.
- Measurable evaluation beats hype.

## Model Maturity Ladder

- Level 0: Scaffold. Schemas, stages, docs, artifacts, and smoke validation exist.
- Level 1: Fixture baseline. Local fixture/seed labels train a small baseline and prove the loop.
- Level 2: Real text benchmark. Human gold text benchmark with train/dev/test splits and regression metrics.
- Level 3: Text+audio benchmark. Aligned audio examples with audio-only and text+audio evaluation.
- Level 4: Text+audio+video benchmark. Aligned video examples with ablation and fusion evaluation.
- Level 5: Cross-domain validated model. Held-out domain transfer results are measured and documented.
- Level 6: Remote-compute scalable training. Reproducible GPU training configs, manifests, MLflow tracking, and artifact sync exist.
- Level 7: Production hardening. Monitoring, calibration, privacy controls, rollout gates, and operational review loops exist.

Current maturity: between Level 0 and Level 1. The pipeline runs and a fixture/seed text baseline exists, but a real benchmark and aligned media set are still required.

## Compute Decision Rules

- Stay local until pipeline, schemas, and evaluation are stable.
- Pay for GPU only once real benchmark data and training configs exist.
- Remote compute is justified when at least one trigger is met:
  - `10k+` text examples.
  - Transformer fine-tuning.
  - Batch audio/video embeddings.
  - `100+` calls with aligned media.
- Do not spend remote compute on scaffolding, unreviewed weak labels, or unaligned media.
