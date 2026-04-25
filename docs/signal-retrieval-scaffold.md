# Signal Retrieval Scaffold

The current retrieval scaffold builds a lightweight local index over the `48` labeled signal examples.

## What It Does

- indexes labeled examples with TF-IDF cosine similarity
- returns top-k similar past examples for a text query
- preserves label, evidence terms, and source file context
- supports reviewer assistance, label consistency checks, and error analysis

## Default Path

- backend: `tfidf_cosine`
- required heavy models: none
- vector database: none
- sentence-transformers: optional later, not required now

## Current Files

- index: `data/nlp_research/signal_retrieval_index.json`
- status: `data/nlp_research/signal_retrieval_status.json`
- query CLI: `python scripts/query_signal_retrieval_index.py --query "pricing objection and competitor pressure" --top-k 3`

## Boundaries

- retrieval is a review aid, not a source of truth
- similarity does not prove label correctness
- the canonical output remains transcript-first deterministic analysis
