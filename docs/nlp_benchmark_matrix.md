# NLP Benchmark Matrix

This matrix is scaffold-only. No models were trained and no external datasets were downloaded.

| Group | Default use | Gate |
| --- | --- | --- |
| Deterministic extraction | canonical baseline | evidence spans and validation |
| Retrieval/RAG | reviewer support | sufficient reviewed labels and provenance-preserving objects |
| External datasets | benchmark-only | local rights check; no gold writes |
| Media | optional support | rights-cleared local/manual media and sparse event windows |
| BYOK LLM reviewer | reviewer/candidate only | fixed bundles, cost/latency logging, no canonical outputs |

External dataset candidates include Financial PhraseBank, FiQA, FinQA, ConvFinQA, FinanceBench, ECTSum, and already configured registry entries. They cannot contaminate gold labels.

## External Benchmark Roles

- Financial PhraseBank: finance sentiment calibration only, not signal extraction gold.
- FiQA: finance sentiment/QA calibration only, not earnings-call guidance-revision gold.
- FinQA: numerical financial QA benchmark, not transcript signal gold.
- ConvFinQA: conversational numerical financial QA benchmark, not transcript signal gold.
- FinanceBench: open-book financial QA/RAG benchmark with questions, answers, and evidence strings; useful for financial QA retrieval evaluation, not earnings-call signal gold.
- ECTSum: earnings-call summarization benchmark, not guidance-revision or analyst-friction gold.
- FinMTEB: financial embedding/retrieval task taxonomy, not proof that dense retrieval works on Signal Engine evidence objects.
- FinBen/Open Financial LLM Leaderboard/FLaME: broad financial LLM benchmark references; forecasting, decision, provider, or leaderboard claims are out of scope.

Benchmark rows cannot promote to gold labels. They can support calibration, regression checks, and comparator reports only.

`src/signal_engine/benchmarks/` now contains a lightweight registry helper for loading benchmark rows, grouping benchmark types, and enforcing no-gold-write/default benchmark-only guardrails. It does not download datasets, train models, or call provider APIs.

For local infrastructure, prefer SQLite for operational audit/review state and Parquet or DuckDB-style local analytical queries only after artifacts are metadata-safe and rights-cleared. BM25 evidence-object retrieval should precede dense retrieval. FAISS or other vector tooling remains optional and gated; managed databases and provider embeddings are not part of this scaffold.

No production ML quality, alpha, trading, or statistical-significance claims are supported.
