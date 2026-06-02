# Reviewed Retrieval Query-Set Process

Status: `retrieval_bakeoff_plan_only`

This process defines how Signal Engine moves from smoke retrieval fixtures toward benchmark-ready retrieval inputs. It does not run providers, generate embeddings, create a vector DB, score retrieval quality, or support production retrieval claims.

## What A Reviewed Query Row Is

A reviewed retrieval query row is metadata only. It links a safe query label to retrieval object metadata IDs and provenance references in `data/retrieval/retrieval_object_metadata.jsonl`.

Required row fields are defined in `schemas/retrieval_reviewed_query_set.schema.json`:

- `query_id`
- `case_id`
- `query_type`
- `query_text_or_safe_query_label`
- `expected_object_ids`
- `expected_object_types`
- `expected_topics`
- `evidence_object_id_refs`
- `provenance_refs`
- `reviewer`
- `reviewed_at`
- `review_status`
- `benchmark_eligible`
- `notes`

Allowed `review_status` values:

- `template_only`
- `smoke_only`
- `review_pending`
- `reviewed`
- `rejected`

Only `review_status=reviewed` with `benchmark_eligible=true` counts toward future benchmark-input readiness.

## Safe Promotion Flow

1. Start from `data/retrieval/retrieval_reviewed_query_set.template.jsonl`.
2. Replace template rows with case-specific rows that reference existing retrieval object IDs.
3. Keep `query_text_or_safe_query_label` metadata/category based. Do not paste transcript, chunk, evidence, or provider response text.
4. Verify each `expected_object_ids` entry exists in `data/retrieval/retrieval_object_metadata.jsonl`.
5. Verify each expected object matches the intended `case_id`, object type, topic, section, speaker role, source hash, text hash, and provenance hash.
6. Verify `provenance_refs` match the referenced retrieval objects.
7. Set `review_status=reviewed`, `reviewer`, and `reviewed_at` only after manual review is complete.
8. Set `benchmark_eligible=true` only for reviewed rows with concrete object references, complete provenance, no placeholders, and no unsafe claim wording.
9. Run the validator before using the query set in any bakeoff plan.

## Readiness Labels

- `template_only`: scaffold rows only; accepted for plan-only checks with `--allow-template`.
- `smoke_only_blocked`: smoke fixtures can exercise wiring but cannot unlock benchmark inputs.
- `review_pending_blocked`: rows still require manual review.
- `reviewed_not_eligible`: reviewed rows exist, but no row is marked eligible.
- `reviewed_eligible_below_minimum`: some rows are eligible, but the first bakeoff minimum is not met.
- `benchmark_ready_inputs_only`: at least 20 reviewed eligible rows are present, object references are known, placeholders are absent, and provenance refs are present. This is only an input-readiness label, not a benchmark result.

## Commands

Validate the template fixture:

```bash
PYENV_VERSION=3.11.3 python tools/validate_retrieval_reviewed_query_set.py \
  --query-set data/retrieval/retrieval_reviewed_query_set.template.jsonl \
  --objects data/retrieval/retrieval_object_metadata.jsonl \
  --allow-template
```

Plan the current local-stub bakeoff wiring:

```bash
PYENV_VERSION=3.11.3 python tools/plan_retrieval_bakeoff.py \
  --manifest configs/retrieval_bakeoff.example.yml \
  --dry-run
```

The plan command must continue to report:

- `network_calls=false`
- `embeddings_generated=false`
- `vector_db_generated=false`
- `benchmark_complete=false`
- `evaluated_retrieval_quality=false`

## Blocked Content

Reviewed query-set rows must not include:

- raw transcript, chunk, evidence, ASR, audio-derived, or provider response text
- generated embeddings, vectors, indexes, or vector-store paths
- answer text or expected-answer leakage
- label, adjudication, training, or promotion semantics
- wording that implies market-performance, causal market reaction, live execution, provider ranking, production retrieval quality, or statistical proof

## Current Limitation

The committed template is intentionally not benchmark-ready. It exists so reviewers can see the required shape and so the bakeoff planner can enforce a stricter query-set gate before any future provider run.
