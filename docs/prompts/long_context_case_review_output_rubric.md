# Long-Context Case Review Output Rubric

Status: template only. This rubric describes future review outputs and is not a model result.

Acceptable future outputs must:

- Follow `schemas/long_context_case_review_output.schema.json`.
- Include `case_id`, `reviewer_model_slot`, and `reviewed_bundle_id`.
- Cite `object_id` refs in `cited_object_refs` for every supported conclusion.
- Cite provenance refs in `cited_provenance_refs` for every supported conclusion.
- Use `abstentions` and `cannot_answer_reasons` when evidence is missing or unsafe.
- Separate detected issues, uncertainty flags, extraction disagreements, and hallucination risk notes.
- Keep `provider_execution=false` and `production_claims=false` in committed examples.

Reject outputs that:

- Include raw transcript text, raw chunk text, raw evidence text, provider responses, embeddings, or vector store content.
- Make trading recommendations, alpha claims, statistical significance claims, production RAG claims, or production retrieval-quality claims.
- Draw uncited conclusions.
- Treat LLM review as canonical extraction.
