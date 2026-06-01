# Retrieval Eval Summary

## Run status
- smoke_metrics: `true`
- evaluated_rag: `false`
- status is `smoke_metrics`.
- manifest_status: `not_provided`
- The scaffold is ready for future reviewed retrieval eval queries only after reviewer-bound evidence IDs replace placeholders and production validation passes.
- This run is not production RAG quality evidence and makes no production retrieval claims.

## Corpus status
- Current status label: `smoke_metrics` unless a completed retrieval eval manifest passes all gates.
- Transcript-aligned evidence remains canonical; audio-only objects are excluded until matched to transcript spans.

## Eval manifest path
- `not_provided`

## Query file path
- `data/retrieval/eval_queries_hd_2025_q4.jsonl`

## Result file path
- `data/retrieval/retrieval_eval_results.jsonl`

## BM25 baseline status
- Metadata-only BM25 smoke path available; no embeddings or vector DB required.

## Object inventory by type
- event_aligned_chunk: `1`
- evidence_object: `1`

## Q&A/no-Q&A state
- `missing`

## Recall@1, recall@3, recall@5
- recall@1: 0.00% (0/8)
- recall@3: 0.00% (0/8)
- recall@5: 0.00% (0/8)

## MRR
- MRR: 0.0000 (0.0000/8)

## Exact evidence ID hit rate
- 0.00% (0/8)

## Citation validity rate
- 100.00% (16/16)

## Invalid citation rate
- 0.00% (0/16)

## Wrong case/ticker/period rates
- wrong_case_rate: 0.00% (0/16)
- wrong_ticker_rate: 0.00% (0/16)
- wrong_period_rate: 0.00% (0/16)

## Abstention correctness
- 100.00% (12/12)

## Fallback overuse rate
- 0.00% (0/8)

## Latency summary
- p50: `None`
- p90: `None`
- p95: `None`
- max: `None`

## Provenance completeness rate
- 100.00% (16/16)

## Pass/warn/fail gate result
- `warn`

## Warnings
- reviewer placeholder expected evidence IDs remain; production metrics must fail closed
- smoke_metrics only; scaffold readiness check, not production RAG quality evidence
- reviewer placeholder expected evidence IDs remain; smoke mode only

## Failures
- none

## Reviewer-support-only statement
- RAG v0 is an evidence-first retrieval evaluation scaffold, not a chatbot, trading system, alpha engine, production retriever quality claim, or production RAG quality evidence.
- No statistical, alpha, trading, live-execution, or market-causality claims are made by this report.
- No labels, gold labels, adjudication rows, training data, promotion candidates, raw transcript text, raw ASR/audio text, chunk text, embeddings, vector DBs, or provider artifacts are produced by this report.
