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
- manifest: `configs/retrieval_bakeoff.first20_reviewed_inputs.example.yml`
- retrieval objects: `data/retrieval/retrieval_object_metadata.jsonl`
- query set: `data/retrieval/retrieval_reviewed_query_set.first20.reviewed_candidate.jsonl`
- provider config: `configs/retrieval_providers.example.yml`
- output root: `/tmp/signal-engine-retrieval-bakeoffs/r13_local_stub_first20_reviewed_inputs_plan`

## Query gate
- query count: `20`
- smoke_only: `false`
- reviewed_query_set: `true`
- query_set_review_stage: `reviewed`
- query_set_readiness_status: `benchmark_ready_inputs_only`
- reviewed eligible query rows: `20`
- minimum reviewed eligible query rows: `20`
- benchmark_threshold_met: `true`
- benchmark-ready inputs only: `true`
- real_benchmark_allowed: `false`
- placeholder references: `0`
- unknown object references: `0`

## Query status counts
- reviewed: `20`

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
- query set: `sha256:a4a3a79fb5367767b8d26f3f0cf3fa78d5c4111eefb9aa1a8e7ae9351d515917`

## Blockers before real benchmark
- reviewer approval required
- real provider config must remain non-committed until approved
- network calls remain disabled in committed scaffold

## Safety
- This plan emits safe plan metadata only.
- Reviewed inputs are ready for a future run: `true`.
- Benchmark execution has not run, provider execution remains disabled, and retrieval quality remains unevaluated.
- It does not generate embeddings, vector stores, provider response payloads, raw text, benchmark scores, labels, adjudication rows, training data, or promotion rows.
- Current status remains plan-only while provider approval, artifact gates, provenance gates, and citation gates block any real benchmark.
