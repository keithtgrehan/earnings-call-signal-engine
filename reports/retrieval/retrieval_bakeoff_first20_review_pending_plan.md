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
- manifest: `configs/retrieval_bakeoff.first20_review_pending.example.yml`
- retrieval objects: `data/retrieval/retrieval_object_metadata.jsonl`
- query set: `data/retrieval/retrieval_reviewed_query_set.first20.jsonl`
- provider config: `configs/retrieval_providers.example.yml`
- output root: `/tmp/signal-engine-retrieval-bakeoffs/r8_local_stub_first20_review_pending_plan`

## Query gate
- query count: `20`
- smoke_only: `false`
- reviewed_query_set: `false`
- query_set_review_stage: `review_pending`
- query_set_readiness_status: `review_pending_blocked`
- reviewed eligible query rows: `0`
- minimum reviewed eligible query rows: `20`
- benchmark_threshold_met: `false`
- benchmark-ready inputs only: `false`
- real_benchmark_allowed: `false`
- placeholder references: `0`
- unknown object references: `0`

## Query status counts
- review_pending: `20`

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
- query set: `sha256:a6885bd6ad52a7b32ef5fe510dcfec8f24b427fb561cbf6a6fe18f9e9503c836`

## Blockers before real benchmark
- benchmark-ready reviewed query-set inputs required
- at least 20 reviewed benchmark-eligible query rows required
- reviewer approval required
- real provider config must remain non-committed until approved
- network calls remain disabled in committed scaffold

## Safety
- This plan emits safe plan metadata only.
- It does not generate embeddings, vector stores, provider response payloads, raw text, benchmark scores, labels, adjudication rows, training data, or promotion rows.
- Current status remains scaffold-only until reviewed query sets, provider approval, artifact gates, provenance gates, and citation gates are complete.
