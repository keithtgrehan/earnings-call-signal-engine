# Case Review Bundle Sidecar Review

Status: simulated sidecar review for Agent R10. The live subagent spawn path was unavailable because the agent thread limit was reached, so the review was performed as three separate checklists and applied before validation.

## Sidecar A: Case-Bundle Schema / Reviewer Usability

Risks found:

- Reviewers need a case-level view without opening raw source files.
- Object refs alone are hard to interpret without query refs, provenance refs, blocked reasons, and safe report links.
- Case ID casing could confuse command usage.

Fixes applied:

- Added `schemas/case_review_bundle.schema.json` with strict metadata-only fields.
- Added case-insensitive `--case-id` handling and deterministic bundle IDs.
- Added Markdown reports and an all-case index with object/query/eligible counts and readiness status.

## Sidecar B: Artifact Safety / No Raw-Data Leakage

Risks found:

- A case bundle could accidentally become a carrier for source excerpts, provider responses, vectors, or benchmark wording.
- Missing provenance would make later long-context review unsafe.
- Cross-case query/object references would make reviewer routing unreliable.

Fixes applied:

- Builder validates retrieval object metadata and reviewed-query rows before bundle creation.
- Bundle validation blocks raw-like fields, provider/vector fields, missing provenance, overclaim flags, and unsafe claim wording.
- Query refs must resolve to object IDs inside the same case bundle.

## Sidecar C: Long-Context Evaluation Readiness

Risks found:

- Case bundles could be mistaken for LLM review readiness or retrieval-quality evidence.
- Current first20 rows are still pending, so real benchmark and provider execution must remain blocked.
- Long-context prompts and reviewer scoring are not implemented yet.

Fixes applied:

- Status label is `case_review_bundle_metadata_only`.
- All generated reports keep provider execution, embeddings, vector DB, evaluated retrieval quality, and production claims false.
- Blocked reasons include review-pending, provider-disabled, LLM-review-disabled, and benchmark-threshold-not-met states.

## Remaining Blockers Before LLM Case Review

- Human review must complete the relevant query rows.
- A gated prompt pack and reviewer adapter still need implementation.
- Faithfulness and citation-quality scoring must be added before any review-quality claim.
- Provider outputs must remain separate and restricted until an approved run path exists.
