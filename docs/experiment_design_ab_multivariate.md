# A/B and Multivariate Experiment Design

Status: evaluation-design scaffold only. These designs do not run live-user experiments, train models, call providers, fetch market data, or support alpha, trading, live execution, causal, production ML, or unsupported statistical-significance claims.

## Variants

- `deterministic_only`: canonical baseline
- `deterministic_plus_retrieval`: deterministic output with provenance-preserving retrieval support
- `deterministic_plus_byok_reviewer`: deterministic output with reviewer/candidate BYOK layer
- `deterministic_plus_audio_metadata`: optional metadata support only
- `deterministic_plus_event_study_context`: exploratory context only

No variant may override deterministic extraction.

## Metrics

Allowed metrics include label agreement with human gold, evidence-span precision, false-positive rate, time-to-review, reviewer disagreement rate, retrieval recall@k, MRR, and calibration/error buckets. Trading or alpha outcome metrics are not primary product claims.

## Multivariate Factors

Candidate factors are chunk type (`evidence_object`, `event_aligned_chunk`, `semantic_chunk`), ranker (`bm25`, optional gated dense, optional gated hybrid), and reviewer mode (`off`, `stub_local`, optional gated BYOK). Each run must preserve provenance and deterministic-first behavior.

## Gates

Experiments must specify sample gates, confounders, outcomes, and stopping rules. Statistical-significance language is disabled unless a separate reviewed-label and power gate is satisfied. The current scaffold keeps `significance_claim_allowed: false`.
