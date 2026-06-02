# Reviewed Query-Set Sidecar Review

Date: 2026-06-02

Status: `retrieval_bakeoff_plan_only`

## Sidecar A: Reviewer Workflow

Findings:

- R6 bakeoff planning was correctly plan-only but still consumed the older smoke eval-query shape.
- R7 needed a separate reviewed-query-set contract with metadata-only object references.
- Positive reviewed rows should bind to retrieval object IDs and provenance refs from `data/retrieval/retrieval_object_metadata.jsonl`.
- Template, smoke, pending, and rejected rows must not unlock benchmark-input readiness.

Fixes applied:

- Added `schemas/retrieval_reviewed_query_set.schema.json`.
- Added `data/retrieval/retrieval_reviewed_query_set.template.jsonl`.
- Added validator logic requiring unique query IDs, known object IDs, provenance refs, reviewer fields for reviewed rows, and eligibility gates.

## Sidecar B: Artifact Safety

Findings:

- Existing retrieval object metadata and provider dry-run gates already reject raw text-like and vector-like payload fields.
- R7 needed stricter query-row checks for raw text fields, evidence text fields, answer leakage, label/adjudication semantics, training semantics, promotion semantics, and generated vector payloads.
- Bakeoff planning should continue to write safe report metadata only.

Fixes applied:

- The reviewed-query validator rejects forbidden keys and transcript-like values.
- Evidence-object refs must point at `evidence_object_metadata` rows when populated.
- Template rows require `--allow-template`.
- Bakeoff reports keep network, embedding, vector DB, benchmark completion, and retrieval-quality flags false.

## Sidecar C: Benchmark-Readiness Labels

Findings:

- The project needed readiness labels that cannot be mistaken for benchmark results.
- A reviewed eligible query set can unlock only future input readiness, not provider ranking or retrieval-quality claims.
- Planner output should show query path, query count, review-status counts, eligible count, placeholder count, unknown object-ref count, and blockers.

Fixes applied:

- Added readiness labels: `template_only`, `smoke_only_blocked`, `review_pending_blocked`, `reviewed_not_eligible`, `reviewed_eligible_below_minimum`, and `benchmark_ready_inputs_only`.
- Added `minimum_reviewed_eligible_queries=20`.
- Updated bakeoff planning to report query-set readiness separately from benchmark completion.

## Remaining Blockers Before Real Provider Bakeoff

- A non-template reviewed query set with at least 20 eligible metadata-only rows is required.
- Reviewer approval is required.
- Real provider config must remain outside committed scaffold config until approved.
- Generated provider artifacts must stay outside the repo and pass artifact safety scans.
- Provider runs must not emit raw text, generated embeddings, vector DBs, labels, adjudication rows, training data, or promotion rows.
