# Long-Context Prompt Pack Sidecar Review

Status: simulated sidecar review for Agent R11. Live subagent spawn was unavailable because the agent thread limit was reached, so the review was performed as three separate checklists and applied before validation.

## Sidecar A: Prompt-Pack Quality / Reviewer Usefulness

Risks found:

- A reviewer needs clear boundaries on allowed inputs before any long-context model is introduced.
- Prompt packets could become too vague if they only link to a bundle without citation and abstention rules.
- The expected output contract needs to be visible before a provider adapter is connected.

Fixes applied:

- Added `schemas/long_context_case_prompt_pack.schema.json` and `schemas/long_context_case_review_output.schema.json`.
- Added prompt-pack JSON and Markdown output with explicit allowed refs, blocked input classes, citation requirements, faithfulness checks, and blocked reasons.
- Added safe prompt templates under `docs/prompts/` with citation, abstention, and output-rubric guidance.

## Sidecar B: Artifact Safety / No Raw-Data Leakage

Risks found:

- Prompt packs could accidentally carry transcript excerpts, chunk text, provider responses, model completions, embeddings, or vector artifacts.
- Generated filenames could imply vector/index/provider artifacts and bypass review.
- Missing provenance refs would make future review packets unsafe.

Fixes applied:

- Builder validates source case bundles and fails closed on raw-like fields, provider/model output fields, embedding/vector fields, missing provenance refs, and unsafe status flags.
- Output paths are limited to JSON/Markdown and reject filenames that imply embeddings, vectors, indexes, provider artifacts, or model output.
- Prompt-pack validation requires provenance refs, retrieval object refs, citation requirements, and false provider/LLM/model-output flags.

## Sidecar C: Evaluation-Readiness / Claim-Safety

Risks found:

- Prompt packs could be mistaken for model outputs or review-quality evidence.
- Current first20 query rows remain review-pending, so long-context review and benchmark gates must remain blocked.
- Claim-boundary wording inside machine-readable payloads must avoid overclaim patterns while still showing the blocked state.

Fixes applied:

- Status label is `long_context_case_prompt_pack_scaffold_only`; index status is `long_context_prompt_pack_index_scaffold_only`.
- Reports state provider execution, LLM calls, model outputs, evaluated model quality, and production claims as false.
- Payload guardrails use deployment-boundary language and validation rejects unsupported production, trading, alpha, and significance wording.

## Remaining Blockers Before Real LLM Review

- Human review must complete and validate the query rows needed for benchmark-ready inputs.
- A provider/model adapter path for long-context review must be added separately and remain disabled by default.
- Reviewer output validation, citation scoring, faithfulness checks, and hallucination-risk reporting must be implemented before any model-quality statement.
- Generated model/provider artifacts must remain outside committed paths unless a future safe artifact class is explicitly approved.
