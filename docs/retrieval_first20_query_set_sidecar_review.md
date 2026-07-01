# First20 Query-Set Sidecar Review

Date: 2026-06-02

Status: `review_pending`

## Sidecar A: Query Quality

Findings:

- A first20 candidate should prove metadata routing and provenance preservation, not semantic retrieval quality.
- Defensible rows should use existing retrieval object IDs and provenance refs only.
- `semantic_chunk_metadata` should not dominate the first candidate because current semantic rows are fallback metadata with unknown section and speaker fields.
- Negative-control and abstention rows need a clearer reviewed-query-set contract before they are mixed into this candidate.

Fixes applied:

- The committed first20 candidate uses known `evidence_object_metadata` rows across multiple tickers and periods.
- Rows include a small mix of `evidence_object_lookup`, `topic_lookup`, `case_comparison_lookup`, `guidance_revision_lookup`, `uncertainty_language_lookup`, and `analyst_pressure_lookup`.
- Every row remains `review_pending` and `benchmark_eligible=false`.

## Sidecar B: Provenance And Object-ID Safety

Findings:

- Object IDs are unique and stable, but text hashes repeat across metadata rows, so `text_hash` must not be used alone as identity.
- Query rows should bind to exact object IDs and provenance refs.
- Extra provenance refs from unrelated cases should be rejected.
- Evidence-object refs should match the row case and have their provenance refs included.

Fixes applied:

- The reviewed-query validator now requires `provenance_refs` to exactly match referenced expected-object provenance refs.
- The validator now rejects cross-case `evidence_object_id_refs`.
- The validator now requires each evidence ref provenance to be present.

## Sidecar C: Reviewer Workflow

Findings:

- Reviewer packets should include metadata rows only and tell reviewers how to inspect spans outside git.
- Review-pending rows must not fake reviewer approval.
- Bakeoff planning should consume the first20 candidate while keeping provider execution and benchmark completion false.

Fixes applied:

- Added `reports/retrieval/retrieval_reviewed_query_set_first20_packet.md`.
- Added `configs/retrieval_bakeoff.first20_review_pending.example.yml`.
- Added explicit `review_stage` handling so review-pending candidates are not mislabeled as smoke fixtures.

## Remaining Blockers Before Real Bakeoff

- Manual review must set `review_status=reviewed`, `reviewer`, and `reviewed_at`.
- Rows must be moved to `benchmark_eligible=true` only after review.
- At least 20 eligible reviewed rows are required before `benchmark_ready_inputs_only`.
- Provider execution must remain disabled until approval and local artifact gates are complete.
- No retrieval-quality or provider-performance claims are supported by this candidate.
