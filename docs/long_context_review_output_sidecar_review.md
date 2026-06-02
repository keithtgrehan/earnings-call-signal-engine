# Long-Context Review Output Sidecar Review

Status: simulated sidecar review for Agent R12. Live subagent spawn was unavailable because the agent thread limit was reached, so the review was performed as three separate checklists and applied before validation.

## Sidecar A: Reviewer-Output Schema / Usability

Risks found:

- A plain free-form review would make citation checks and abstention checks brittle.
- A reviewer needs a clear way to provide metadata-only conclusions without copying source content.
- Batch validation needs stable counters for reviewer handoff and future scoring work.

Fixes applied:

- Added structured `conclusions` with per-conclusion `cited_object_refs` and `cited_provenance_refs`.
- Added structured `abstentions` plus `cannot_answer_reasons` for explicit abstain behavior.
- Added validation summaries with record, citation, abstention, and unsupported-claim counts.

## Sidecar B: Artifact Safety / No Raw Text Or Model-Output Leakage

Risks found:

- Future reviewer-output files could accidentally carry raw source excerpts, provider responses, model completions, chain-of-thought, embeddings, or vector artifacts.
- Output reports could become a back door for raw model output if filenames or fields are not constrained.
- Candidate files may use JSON or JSONL, so both paths need the same safety checks.

Fixes applied:

- Validator rejects raw-like fields, provider/model output fields, chain-of-thought or trace fields, embeddings, vectors, and unsafe payload keys across JSON and JSONL records.
- Validation report paths are limited to JSON/Markdown and reject filenames suggesting provider/model/vector artifacts.
- Committed sample candidates are metadata-only and marked `sample_only=true`.

## Sidecar C: Evaluation-Readiness / Claim-Safety

Risks found:

- Passing validation could be mistaken for review correctness or model quality.
- Current reviewed query rows are still blocked, so long-context scoring and provider runs must remain disabled.
- Unsafe financial, production, or benchmark wording must fail before reports are written.

Fixes applied:

- Status label is `long_context_review_output_validation_only`.
- All reports keep provider execution, LLM calls, model output, evaluated model quality, benchmark completion, and production claims false.
- Validator rejects trading, alpha, unsupported statistical, production RAG, production retrieval, benchmark result, and model-quality claim wording.

## Remaining Blockers Before Real LLM Review Or Scoring

- Human review must complete the query rows needed for benchmark-ready inputs.
- Provider/model execution needs a separate approved manifest and local artifact location outside committed restricted paths.
- Faithfulness, citation-quality, abstention-correctness, and hallucination-risk scoring are still future work.
- No reviewer-output candidate should be treated as a label, gold label, adjudication row, training row, promotion row, benchmark score, or production evidence.
