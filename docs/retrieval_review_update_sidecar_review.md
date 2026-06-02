# Retrieval Review Update Sidecar Review

Status: simulated sidecar review for Agent R9. The in-session sidecar spawn was unavailable because the agent thread limit was reached, so the review was performed as three independent checklists and applied to the implementation.

## Sidecar A: Reviewer UX / Update Workflow

Risks found:

- Reviewers need a CSV surface that is easier to edit than JSONL but must not expose source excerpts.
- JSON-array metadata columns can be accidentally edited by spreadsheet software.
- A reviewer could try to overwrite the original first20 JSONL.

Fixes applied:

- Added `tools/export_retrieval_review_worksheet.py` with fixed metadata-only columns.
- Added import immutability checks for query ID, case ID, query type, object IDs, object types, and provenance refs.
- Added an import guard that rejects output paths equal to the source query set.

## Sidecar B: Safety / Eligibility Gate

Risks found:

- Reviewer notes could become a raw-content leakage path.
- A row could claim benchmark eligibility without complete reviewer metadata.
- Changed object/provenance refs could silently corrupt future bakeoff inputs.

Fixes applied:

- Added safety validation over worksheet headers and values, including raw-like fields, answer leakage wording, unsafe claim wording, and provider/vector artifact keys.
- Required `review_status=reviewed`, reviewer, ISO timestamp, and `reviewer_decision=approved` before `benchmark_eligible=true`.
- Revalidates the imported candidate with the existing reviewed-query-set validator before writing the summary.

## Sidecar C: Benchmark-Readiness / Status Labels

Risks found:

- Threshold readiness could be confused with benchmark completion.
- Import summaries could look like retrieval-quality evidence.
- Generated files could imply provider execution or vector output.

Fixes applied:

- Import summary uses `retrieval_review_import_only`.
- Summary reports explicitly keep provider execution, embeddings, vector DB, benchmark completion, evaluated retrieval quality, and production RAG claim false.
- Output filename guard rejects embedding, vector, index, FAISS, Chroma, LanceDB, and provider-artifact names.

## Remaining Blockers Before Real Bakeoff

- Human reviewers still need to complete the first20 worksheet without copying source excerpts into notes.
- A benchmark-eligible candidate must be produced and validated.
- Provider execution remains disabled until a separately reviewed bakeoff manifest allows it.
- Generated provider artifacts must remain outside committed repo paths.
