# Retrieval Evidence Benchmark Policy

Retrieval must be evidence-object first:

1. Evidence objects
2. Event-aligned chunks
3. Semantic chunks

Default local checks do not build embeddings, vector DBs, provider reranker calls, or full raw text artifacts.

Metrics:

- recall@k
- MRR
- evidence-ID hit rate
- citation validity
- blocked-source count
- latency
- reviewer usefulness

FinanceBench and FinMTEB are references for benchmark design only; they are not Signal Engine gold labels.
