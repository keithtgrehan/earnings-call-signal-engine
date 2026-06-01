# Retrieval Eval Query Promotion Process

Status: documented process only. This does not create gold labels, adjudication rows, training data, provider downloads, embeddings, vector stores, or raw transcript artifacts.

Use this process when moving a smoke query from `data/retrieval/eval_queries_hd_2025_q4.jsonl` or `data/retrieval/eval_queries_first30_template.jsonl` into a reviewed retrieval eval query set.

## Preconditions

- The case has transcript-aligned evidence objects or event-aligned chunks with source, normalized transcript, and provenance hashes.
- The reviewer has inspected the transcript span outside git and selected the evidence object ID or event-aligned chunk ID.
- Q&A state is explicit: present, missing, or unavailable for the case.
- Audio-only support objects are excluded unless they are matched to transcript spans.
- The query remains metadata/category based and contains no raw transcript text, ASR text, audio-derived text, chunk text, or copied retrieval payload text.

## Review Steps

1. Copy the smoke query into a new reviewed query JSONL outside the smoke-only file.
2. Replace placeholder IDs such as `REVIEW_REQUIRED_HD_2025_Q4_EVIDENCE_ID` or `{reviewed_evidence_id}` with reviewer-bound retrieval object IDs.
3. Keep negative-control rows with `expected_evidence_ids=[]`, `negative_control=true`, and `abstention_expected=true`.
4. Confirm `expected_object_types`, `expected_sections`, `expected_speaker_roles`, and `rights_required` match the reviewed object metadata.
5. Run the retrieval evaluator in production mode and require placeholder checks, raw-text checks, provenance checks, abstention checks, fallback-overuse checks, recall@5, MRR, invalid-citation rate, and citation-validity gates to pass.
6. Record the completed retrieval eval manifest path in the report only after the production run finishes.

## Blocks

- Do not use this process to create labels, gold labels, adjudication rows, training data, or promotion rows.
- Do not paste raw transcript excerpts, ASR output, audio-derived wording, chunk body text, embedding payloads, vector data, or provider artifacts into query or result files.
- Do not use vendor disclaimers, safe-harbor boilerplate, operator-only lines, non-GAAP boilerplate, semantic fallback, or audio-unmatched material as source-backed signal evidence.
- Do not make statistical, alpha, trading, live-execution, or market-causality claims from retrieval metrics.

## Status Language

- HD one-transcript runs remain `smoke_metrics`.
- Reviewed query files with placeholders removed are scaffold-readiness inputs until a completed manifest passes all gates.
- `evaluated_rag=false` remains the default status field until the repository has a completed retrieval eval manifest and every gate passes.
