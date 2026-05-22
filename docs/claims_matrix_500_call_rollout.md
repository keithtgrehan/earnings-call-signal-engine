# Claims Matrix for 500-Call Rollout

## Supported

- Signal Engine is transcript-first.
- Deterministic extraction is the canonical baseline.
- Rights registry validation fails closed for unknown or restricted sources.
- Manual-local files can be registered as metadata without copying raw files.
- Retrieval objects preserve provenance and rights fields.

## Gated

- Retrieval/reranking quality claims require reviewed-label volume and fixed benchmarks.
- BYOK LLM review requires provider config, cost/latency logging, and fixed bundles.
- ASR/video review requires rights-cleared local/manual media.
- Event-study summaries require event date, event window, estimation window, expected return model, AR/CAR definitions, controls, and sufficient reviewed-label coverage.

## Not Supported

- No alpha or trading-performance claims.
- No live execution.
- No production ML claims.
- No unsupported statistical-significance claims.
- No causal claims from event-study outputs.
- No external dataset or weak-label promotion into gold.

## Agent 2 Claim Rules

Event-study outputs may report exploratory abnormal return and cumulative abnormal return distributions when controls and coverage are documented. In this scaffold they must not be framed as trading performance, alpha, causality, or statistically significant results; any future stronger claim would require sufficient sample size, controls, and reviewed-label quality.

## Agent 5 Claim Rules

Acquisition reports may claim metadata readiness, blocked-case tracking, and rights-gated registration. They must not imply raw acquisition, download completion, license clearance, or media availability unless those fields are explicitly present in the registry.
