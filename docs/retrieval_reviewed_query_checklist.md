# Reviewed Retrieval Query Checklist

Use this checklist before changing any row to `review_status=reviewed` or `benchmark_eligible=true`.

## Query Row

- The row uses the reviewed-query schema, not the older smoke eval-query schema.
- `query_id` is unique and stable.
- `case_id` matches every referenced retrieval object.
- `query_text_or_safe_query_label` is a safe metadata/category label, not pasted transcript wording.
- `query_type` describes the retrieval behavior being checked.
- `expected_object_ids` is non-empty and contains only known retrieval object metadata IDs.
- `expected_object_types` matches the referenced retrieval objects.
- `expected_topics` is metadata only.
- `evidence_object_id_refs` contains only known evidence-object metadata IDs when populated.
- `provenance_refs` includes the provenance refs from the referenced retrieval objects.
- `notes` contains review rationale only, not source text.

## Retrieval Object Reference

- Object ID exists in `data/retrieval/retrieval_object_metadata.jsonl`.
- Object type is one of `semantic_chunk_metadata`, `event_aligned_chunk_metadata`, or `evidence_object_metadata`.
- `content_included=false`, `embeddings_included=false`, and `vector_db_included=false`.
- Source hash, text hash, normalized transcript hash, and provenance hash are present.
- Speaker role, section label, topic, ticker, and fiscal period match the reviewer intent.
- Q&A-specific rows remain blocked unless the case has Q&A state.
- Safe-harbor, non-GAAP, operator-only, vendor-disclaimer, semantic-fallback, and audio-unmatched objects are not treated as transcript-aligned signal evidence.

## Reviewer Gate

- `review_status=reviewed` has a non-empty `reviewer`.
- `reviewed_at` uses `YYYY-MM-DDTHH:MM:SSZ`.
- `benchmark_eligible=true` is used only with `review_status=reviewed`.
- Placeholder IDs and template labels are removed.
- The row does not include answer leakage, label/adjudication semantics, training semantics, promotion semantics, generated vectors, or provider payload fields.
- The row does not imply production retrieval quality, provider performance ranking, market-use guidance, market causality, or statistical proof.

## Before A Future Bakeoff

- At least 20 reviewed eligible rows exist.
- The reviewed query-set validator passes without `--allow-template`.
- The bakeoff planner reports `benchmark_ready_inputs_only`.
- Provider execution remains disabled until reviewer approval, local artifact paths outside the repo, and artifact safety checks are in place.
