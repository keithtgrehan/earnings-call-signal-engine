# Retrieval Review Update Workflow

Status: reviewer update/import path only.

This workflow makes `data/retrieval/retrieval_reviewed_query_set.first20.jsonl` reviewable without editing the JSONL directly. It exports a metadata-only CSV worksheet, imports only reviewer/status decisions, and writes a separate candidate JSONL. It does not run providers, create embeddings, create vector stores, produce benchmark scores, or support production retrieval claims.

## Export Worksheet

```bash
PYENV_VERSION=3.11.3 python tools/export_retrieval_review_worksheet.py \
  --query-set data/retrieval/retrieval_reviewed_query_set.first20.jsonl \
  --objects data/retrieval/retrieval_object_metadata.jsonl \
  --out reports/retrieval/retrieval_review_worksheet_first20.csv
```

The worksheet contains only metadata fields:

- `query_id`
- `case_id`
- `query_type`
- `expected_object_ids`
- `expected_object_types`
- `evidence_object_id_refs`
- `provenance_refs`
- `review_status`
- `benchmark_eligible`
- `reviewer`
- `reviewed_at`
- `reviewer_decision`
- `reviewer_notes`
- `rejection_reason`

The worksheet intentionally omits source excerpts, answer text, embeddings, vectors, provider responses, labels, adjudication fields, training fields, and promotion fields.

## Fill Reviewer Decisions

Allowed reviewer fields are:

- `review_status`
- `benchmark_eligible`
- `reviewer`
- `reviewed_at`
- `reviewer_decision`
- `reviewer_notes`
- `rejection_reason`

Do not change:

- `query_id`
- `case_id`
- `query_type`
- `expected_object_ids`
- `expected_object_types`
- `evidence_object_id_refs`
- `provenance_refs`

For a benchmark-eligible row, all of the following must be true:

- `review_status=reviewed`
- `benchmark_eligible=true`
- `reviewer` is present
- `reviewed_at` uses `YYYY-MM-DDTHH:MM:SSZ`
- `reviewer_decision=approved`
- referenced object IDs and provenance refs still validate against `data/retrieval/retrieval_object_metadata.jsonl`

Rows that remain pending should keep `review_status=review_pending`, `benchmark_eligible=false`, empty `reviewer`, empty `reviewed_at`, and empty `reviewer_decision`.

## Import Updates

```bash
PYENV_VERSION=3.11.3 python tools/import_retrieval_review_updates.py \
  --query-set data/retrieval/retrieval_reviewed_query_set.first20.jsonl \
  --review-updates reports/retrieval/retrieval_review_worksheet_first20.csv \
  --objects data/retrieval/retrieval_object_metadata.jsonl \
  --out data/retrieval/retrieval_reviewed_query_set.first20.reviewed_candidate.jsonl
```

The import matches rows only by `query_id`. It fails closed if row count changes, query IDs are duplicated, immutable fields change, unsafe fields appear, eligibility is overclaimed, reviewer metadata is missing, or any candidate row fails the existing reviewed-query-set validator.

The original first20 JSONL is not overwritten by default.

## Readiness Versus Benchmark Completion

Meeting the reviewed-row threshold only means the query-set inputs are ready for a future bakeoff gate. It does not mean a bakeoff has run.

Required status boundaries:

- benchmark complete: `false`
- provider execution: `false`
- embeddings generated: `false`
- vector DB generated: `false`
- evaluated retrieval quality: `false`
- production RAG claim: `false`

Before any real provider bakeoff, a separate approved manifest must enable the provider slot, network permissions, artifact location outside committed paths, and reviewer approval.
