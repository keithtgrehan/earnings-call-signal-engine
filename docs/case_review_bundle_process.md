# Case Review Bundle Process

Status: `case_review_bundle_metadata_only`.

A case review bundle is a metadata-only package for one earnings-call case. It collects retrieval object references, reviewed-query references, provenance references, and safe report links so a reviewer can see whether a case is ready for later bounded long-context review.

It is not an LLM output, retrieval benchmark, provider run, label file, adjudication artifact, training set, or production-quality claim.

## Build One Bundle

```bash
PYENV_VERSION=3.11.3 python tools/build_case_review_bundle.py \
  --case-id HD_2025_Q4 \
  --objects data/retrieval/retrieval_object_metadata.jsonl \
  --query-set data/retrieval/retrieval_reviewed_query_set.first20.jsonl \
  --out reports/case_bundles/HD_2025_Q4.case_review_bundle.json \
  --report reports/case_bundles/HD_2025_Q4.case_review_bundle.md
```

The command accepts case IDs case-insensitively and writes JSON plus Markdown. The JSON is strict metadata: object IDs, hashes, provenance refs, query IDs, review status, and readiness flags only.

## Build All Bundles

```bash
PYENV_VERSION=3.11.3 python tools/build_case_review_bundle.py \
  --all-cases \
  --objects data/retrieval/retrieval_object_metadata.jsonl \
  --query-set data/retrieval/retrieval_reviewed_query_set.first20.jsonl \
  --out-dir reports/case_bundles
```

This writes one bundle per case in the retrieval object metadata inventory and an index:

- `reports/case_bundles/case_review_bundle_index.json`
- `reports/case_bundles/case_review_bundle_index.md`

## Validate Bundle Or Index

```bash
PYENV_VERSION=3.11.3 python tools/build_case_review_bundle.py \
  --validate reports/case_bundles/case_review_bundle_index.json
```

Validation fails closed on missing provenance, raw-like fields, provider output fields, embedding/vector fields, overclaiming status flags, and benchmark/result wording.

## Current Readiness Boundary

Current first20 reviewed-query rows remain review-pending. Case bundles can show which cases have retrieval objects and query rows, but they do not unlock real provider or LLM review.

Required false flags:

- `provider_execution=false`
- `embeddings_generated=false`
- `vector_db_generated=false`
- `evaluated_retrieval_quality=false`
- `production_claims=false`

## Before LLM Case Review

Before any long-context reviewer is enabled:

- deterministic extraction remains canonical
- source/provenance metadata must remain intact
- reviewed query rows must be human-approved where benchmark readiness is needed
- LLM prompts must use a separate gated prompt pack
- provider configuration and generated artifacts must stay outside committed paths unless explicitly safe
- outputs must be scored for faithfulness and citation quality before any quality claim
