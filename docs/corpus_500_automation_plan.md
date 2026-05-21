# 500-Call Corpus Automation Plan

This is a scaffold-only plan for rights-safe corpus automation. No real acquisition, raw transcript copying, audio/video download, model training, or external API call has happened in this rollout.

## Automation Path

1. Register candidate calls as metadata records.
2. Classify source rights in `configs/resource_registry.example.yml` or a local registry.
3. Fail closed on unknown, paywalled, login-gated, vendor, or unchecked terms.
4. Register manual-local transcript/audio/video file paths without copying raw files into the repo.
5. Build transcript-first artifacts only after rights and provenance are explicit.
6. Export semantic chunks, event-aligned chunks, and evidence objects with provenance and rights fields.
7. Run deterministic extraction before retrieval, reranking, LLM review, or model benchmarks.

## Built vs Scaffolded

- Built: safe registry validation, restricted artifact checking, retrieval schema validation, benchmark registry validation, BYOK config validation, and Make check targets.
- Scaffolded: YouTube metadata registration, licensed vendor placeholder, manual-local file registration, benchmark registry, BYOK reviewer config.
- Gated: raw ingest, ASR, sparse video review, retrieval/reranking experiments, BYOK LLM review.

## Not Supported

- No live trading, alpha, execution, production ML, or unsupported statistical-significance claims.
- No full-call multimodal brute force.
- No external dataset or weak-label promotion into gold.
