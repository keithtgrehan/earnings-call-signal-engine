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

No production ML quality, alpha, trading, or statistical-significance claims are supported.
