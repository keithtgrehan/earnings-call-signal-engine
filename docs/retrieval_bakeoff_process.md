# Retrieval Bakeoff Process

Status: `retrieval_bakeoff_plan_only`.

Current flags:
- network_calls: `false`
- embeddings_generated: `false`
- vector_db_generated: `false`
- benchmark_complete: `false`
- evaluated_retrieval_quality: `false`

This control plane validates and plans future retrieval bakeoffs. It does not run providers, generate embeddings, create vector stores, compute benchmark metrics, or support production retrieval/RAG claims.

## Default Commands

```bash
PYENV_VERSION=3.11.3 python tools/export_retrieval_object_metadata.py --validate-jsonl data/retrieval/retrieval_object_metadata.jsonl
PYENV_VERSION=3.11.3 python tools/run_retrieval_provider_dry_run.py --config configs/retrieval_providers.example.yml --objects data/retrieval/retrieval_object_metadata.jsonl --dry-run
PYENV_VERSION=3.11.3 python tools/validate_retrieval_bakeoff_manifest.py --manifest configs/retrieval_bakeoff.example.yml
PYENV_VERSION=3.11.3 python tools/plan_retrieval_bakeoff.py --manifest configs/retrieval_bakeoff.example.yml --dry-run
```

## Reviewer Map

- Bakeoff manifest schema: `schemas/retrieval_bakeoff_manifest.schema.json`
- Example bakeoff manifest: `configs/retrieval_bakeoff.example.yml`
- Provider config: `configs/retrieval_providers.example.yml`
- Query promotion gate: `docs/retrieval_eval_query_promotion_process.md`
- Manifest validator: `tools/validate_retrieval_bakeoff_manifest.py`
- Bakeoff planner: `tools/plan_retrieval_bakeoff.py`
- Plan reports: `reports/retrieval/retrieval_bakeoff_plan.json` and `reports/retrieval/retrieval_bakeoff_plan.md`

## Reviewed Query Gate

The example manifest uses the HD smoke query file and marks it `smoke_only=true`. This permits plan-only validation but blocks real benchmark status.

A real bakeoff requires:
- a reviewed retrieval eval query set
- concrete reviewer-bound evidence IDs for positive rows
- no placeholder evidence IDs
- negative controls with empty `expected_evidence_ids`, `negative_control=true`, and `abstention_expected=true`
- no raw transcript text, chunk text, answer leakage, labels, adjudication rows, training data, or promotion rows

## Local Artifact Boundary

Committed plan reports may live under `reports/retrieval/`. Generated provider artifacts must use a local-only output root outside committed repo paths, such as `/tmp/signal-engine-retrieval-bakeoffs/<bakeoff_id>/`.

Blocked from commits:
- embeddings and vector stores
- FAISS, Chroma, LanceDB, SQLite, DB, Parquet, NumPy, or index artifacts
- provider response payloads
- raw transcript text, raw ASR/audio text, chunk text, labels, adjudication rows, training data, and promotion rows

## Planned Metrics

The plan lists metrics as planned only: recall@1/3/5, MRR, exact evidence ID hit rate, citation validity, invalid citation, wrong case/ticker/period, abstention correctness, fallback overuse, latency summaries, and provenance completeness. The plan does not compute these metrics.

## Reviewer Decision

Current output supports scaffold readiness only. It does not support provider ranking, provider performance, production retrieval quality, production RAG, trading, alpha, or significance claims.
