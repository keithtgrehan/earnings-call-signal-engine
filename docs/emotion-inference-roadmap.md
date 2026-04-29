# Emotion Inference Roadmap

Signal Engine 2.0 keeps deterministic, evidence-backed outputs as the canonical layer. Transcript evidence, rule-based scoring, and reproducible metadata remain the source of truth even as the roadmap expands toward text, audio, video, and later multimodal fusion.

## Canonical Rule

- Deterministic transcript-first outputs remain canonical.
- Optional models are enrichment or benchmark candidates only.
- No black-box score becomes canonical without explicit evidence linkage and repeatable evaluation.
- No truth-detection or lie-detection claims are made anywhere in this roadmap.

## Text Emotion Benchmark Approach

- Start with transcript segments and human-readable labels.
- Treat emotion models as benchmark baselines, not final adjudicators.
- Compare candidates against tiny synthetic fixtures first, then against approved external datasets later.
- Report confusion matrices, macro F1, simple calibration summaries, and inter-rater agreement where labels are subjective.
- Keep outputs inspectable at the utterance level so every score can be traced back to transcript evidence.

## Audio Emotion Feature Plan

- Keep audio optional and off by default.
- Prioritize feature extraction over end-to-end emotion claims in the first phase.
- Use engineered cues such as pauses, energy, pitch, speaking rate, and stability as review inputs.
- Treat ASR, diarization, and prosody as separate optional layers so each can be benchmarked independently.
- Preserve transcript-first fallback behavior when audio tooling is unavailable.

## Video Escalation Rule

- Video analysis is escalation-only, never the default path.
- Use video tooling for keyframes, scenes, and context review on already-flagged interactions.
- Do not convert visual signals into standalone truth claims.
- Require transcript and, where possible, audio evidence before drawing user-facing conclusions.

## Privacy And PII

- Privacy review is required before any customer or employee conversation data enters benchmark workflows.
- PII detection and anonymization should remain optional, local, and auditable.
- External datasets must be checked for license terms, redistribution limits, and downstream use restrictions.
- Synthetic fixtures remain the safest default for local smoke tests.

## Benchmark Methodology

- Benchmark models against public references only after deterministic baseline behavior is stable.
- Separate benchmark references, dataset cards, and runtime adapters so no dataset or model download happens implicitly.
- Report both benchmark quality and operational risk: install weight, tokens, gating, runtime cost, and privacy exposure.
- Validate domain transfer carefully across support QA, sales, account management, and earnings-call reference workflows.

## Known Limitations

- Emotion labels are inherently subjective and often depend on context outside a single utterance.
- Public datasets rarely match enterprise call structure, incentives, or privacy constraints.
- Audio quality, accents, crosstalk, and speaker overlap can distort speech-derived proxies.
- Video benchmarks are even less representative of real support and revenue conversations.
- Benchmark improvements do not automatically justify product inclusion.

## Explicit Non-Claims

- This roadmap does not claim to detect truthfulness, deception, or hidden intent with certainty.
- This roadmap does not elevate model emotion scores above transcript evidence.
- This roadmap does not require heavyweight models, external APIs, or bundled datasets to use Signal Engine 2.0 today.
