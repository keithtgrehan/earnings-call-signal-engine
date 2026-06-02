# Long-Context Case Review User Prompt Template

Status: template only. Do not call an LLM from this file.

Review the supplied case prompt pack:

- `prompt_pack_id`: `{prompt_pack_id}`
- `case_id`: `{case_id}`
- `source_case_bundle_path`: `{source_case_bundle_path}`
- `allowed_input_refs`: `{allowed_input_refs}`
- `blocked_input_types`: `{blocked_input_types}`
- `citation_requirements`: `{citation_requirements}`
- `faithfulness_checks`: `{faithfulness_checks}`

Use only the provided bundle refs. Do not paste raw transcript text, raw chunk text, or raw evidence text into the prompt or response.

Return a metadata-only review object following `schemas/long_context_case_review_output.schema.json`.

Reviewer tasks:

- Identify missing or blocked inputs.
- Check whether each conclusion can cite at least one `object_id` and one provenance ref.
- Abstain on unsupported questions and list cannot-answer reasons.
- Flag possible extraction disagreements without overriding deterministic extraction.
- Do not provide trading recommendations, alpha claims, statistical significance claims, production RAG claims, or production retrieval-quality claims.
