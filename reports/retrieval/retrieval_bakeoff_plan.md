# Retrieval Bakeoff Plan

## Run status
- status: `retrieval_bakeoff_plan_only`
- network calls: `false`
- embeddings generated: `false`
- vector DB generated: `false`
- benchmark complete: `false`
- evaluated retrieval quality: `false`
- production RAG claim: `false`

## Inputs
- manifest: `configs/retrieval_bakeoff.example.yml`
- retrieval objects: `data/retrieval/retrieval_object_metadata.jsonl`
- query set: `data/retrieval/eval_queries_hd_2025_q4.jsonl`
- provider config: `configs/retrieval_providers.example.yml`
- output root: `/tmp/signal-engine-retrieval-bakeoffs/r6_local_stub_smoke_plan`

## Query gate
- query count: `20`
- smoke_only: `true`
- reviewed_query_set: `false`
- real_benchmark_allowed: `false`

## Provider slots
- `local_stub`

## Planned metrics
- `recall@1`
- `recall@3`
- `recall@5`
- `mrr`
- `exact_evidence_id_hit_rate`
- `citation_validity_rate`
- `invalid_citation_rate`
- `wrong_case_rate`
- `wrong_ticker_rate`
- `wrong_period_rate`
- `abstention_correctness`
- `fallback_overuse_rate`
- `latency_p50`
- `latency_p90`
- `latency_p95`
- `latency_max`
- `provenance_completeness_rate`

## Metadata digests
- retrieval objects: `sha256:9b6171fdc59d77e08d8b2ba53328a43a1556f749c657d0462ce3f20a1d11e779`
- query set: `sha256:f0fe1bd46f44077f6e3efacdd2c1c0cc9f8c0c3ad12bb5ad51511a9ecdc9425e`

## Blockers before real benchmark
- reviewed retrieval eval query set required
- reviewer approval required
- real provider config must remain non-committed until approved
- network calls remain disabled in committed scaffold

## Safety
- This plan emits safe plan metadata only.
- It does not generate embeddings, vector stores, provider response payloads, raw text, benchmark scores, labels, adjudication rows, training data, or promotion rows.
- Current status remains scaffold-only until reviewed query sets, provider approval, artifact gates, provenance gates, and citation gates are complete.
