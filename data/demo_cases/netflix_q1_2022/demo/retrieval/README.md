# netflix_q1_2022 retrieval bundle

This folder contains a supporting-only retrieval sidecar derived from deterministic case artifacts.

Contents:
- `netflix_retrieval_rows.jsonl`: normalized retrieval rows with per-row provenance metadata
- `netflix_retrieval_manifest.json`: bundle metadata, source-type counts, and embedding status
- `netflix_retrieval_embeddings.npy`: optional row embedding matrix aligned 1:1 with the rows file

Boundary notes:
- deterministic transcript-backed artifacts remain canonical
- chunking remains the bounded review unit
- lexical and semantic retrieval are navigation aids only
- similarity does not replace transcript-backed review
