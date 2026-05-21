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

## Not Supported

- No alpha or trading-performance claims.
- No live execution.
- No production ML claims.
- No unsupported statistical-significance claims.
- No external dataset or weak-label promotion into gold.
