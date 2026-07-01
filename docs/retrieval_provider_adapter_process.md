# Retrieval Provider Adapter Process

Status: `retrieval_provider_adapter_scaffold_only`.

This layer defines where future embedding and reranking providers plug in. It is adapter foundation only. It does not run a provider benchmark, generate embeddings, create a vector DB, call provider APIs, evaluate retrieval quality, or make production retrieval/RAG claims.

## Status Flags

- evaluated_retrieval_quality: `false`
- embeddings_generated: `false`
- vector_db_generated: `false`
- network_calls: `false`
- provider_benchmark_complete: `false`
- production_rag_claim: `false`

## Reviewer Map

- Config schema: `schemas/retrieval_provider_config.schema.json`
- Example config: `configs/retrieval_providers.example.yml`
- Provider interfaces and run metadata: `src/signal_engine/retrieval/providers/adapters.py`
- Config validation: `src/signal_engine/retrieval/providers/config.py`
- Path and payload safety gates: `src/signal_engine/retrieval/providers/safety.py`
- Dry-run stubs: `src/signal_engine/retrieval/providers/stubs.py`
- Dry-run CLI: `tools/run_retrieval_provider_dry_run.py`
- Safe outputs: `reports/retrieval/retrieval_provider_dry_run.json` and `reports/retrieval/retrieval_provider_dry_run.md`

## Default Dry Run

```bash
PYENV_VERSION=3.11.3 python tools/run_retrieval_provider_dry_run.py \
  --config configs/retrieval_providers.example.yml \
  --objects data/retrieval/retrieval_object_metadata.jsonl \
  --dry-run
```

The default config enables only `local_stub`. External embedding and reranking provider slots are represented but disabled. Tests and default runs require no API keys and make no network calls.

## Future Provider Enablement

Before enabling a real provider, create a non-committed local config and keep generated provider artifacts outside the repo. The committed example config must remain fail-closed: `local_stub` default, `network_enabled=false`, real provider slots disabled, and output paths limited to safe report metadata.

Any future provider execution must:
- validate metadata-only retrieval objects first
- use reviewed retrieval eval queries
- write to a safe non-committed output location
- avoid committing embeddings, vector stores, provider responses, raw payload text, labels, adjudication rows, training data, or promotion rows
- rerun restricted artifact and transcript-text staged checks before any commit

## Future Bakeoff Gate

A later bakeoff may compare providers only after reviewed eval queries and pass/fail gates exist. Evidence required before changing status from scaffold to benchmarked includes completed run metadata, reviewed retrieval eval queries, raw-text leak checks, provenance completeness checks, invalid-citation checks, abstention checks, and artifact scans.

Until those gates exist and pass, do not describe this layer as evaluated retrieval, production RAG, provider performance, reranker performance, embedding baseline results, or a completed provider bakeoff.
