# Retrieval Object Metadata Export Process

Status: `retrieval_object_scaffold_only`.

This path exports metadata-only retrieval objects that can later support embedding or reranking experiments. It does not create embeddings, vector databases, labels, adjudication rows, training data, promotion rows, raw transcript text, ASR/audio text, chunk body text, or provider artifacts.

## Allowed Output

The committed JSONL export may contain only:
- stable retrieval object IDs
- object type, case, ticker, company, and fiscal-period metadata
- source type
- provenance references
- source, text, normalized-transcript, and provenance hashes
- section, speaker-role, topic, span, rights, priority, and false content/vector flags

Allowed `object_type` values are:
- `semantic_chunk_metadata`
- `event_aligned_chunk_metadata`
- `evidence_object_metadata`

## Validation Gate

Before using an existing export as input to later experiments, run:

```bash
PYENV_VERSION=3.11.3 python tools/export_retrieval_object_metadata.py --validate-jsonl data/retrieval/retrieval_object_metadata.jsonl
```

The validation mode fails closed on schema errors, duplicate object IDs, unstable object IDs, missing provenance, missing hash fingerprints, raw text-like fields, embedding/vector fields, and count inconsistencies in the generated summary.

## Report Consistency

The report at `reports/retrieval/retrieval_object_metadata_export.md` must be regenerated from the exporter and kept consistent with the JSONL row count, counts by `object_type`, and counts by `case_id`.

```bash
PYENV_VERSION=3.11.3 python tools/export_retrieval_object_metadata.py
```

## Later Experiment Boundary

Embedding or reranking experiments may read the metadata JSONL, but generated embeddings, vector stores, raw payload text, provider artifacts, labels, adjudication rows, training data, and promotion rows must remain outside committed artifacts unless a later explicit gate permits a safe metadata-only artifact.

This export is scaffold readiness only. It is not retrieval-quality evidence and makes no production retrieval claims, trading claims, alpha claims, statistical-significance claims, or live-execution claims.
