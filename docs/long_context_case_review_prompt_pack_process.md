# Long-Context Case Review Prompt Pack Process

Status: `long_context_case_prompt_pack_scaffold_only`.

A long-context prompt pack is a metadata-only packet for future bounded case review. It consumes a case review bundle and packages reviewer instructions, allowed references, blocked input classes, citation requirements, faithfulness checks, and an expected output schema reference.

It is not a provider run, LLM call, model output, benchmark, label file, adjudication artifact, training set, or retrieval-quality claim.

## Build One Prompt Pack

```bash
PYENV_VERSION=3.11.3 python tools/build_long_context_prompt_pack.py \
  --bundle reports/case_bundles/HD_2025_Q4.case_review_bundle.json \
  --out reports/long_context/HD_2025_Q4.prompt_pack.json \
  --report reports/long_context/HD_2025_Q4.prompt_pack.md
```

The builder validates the source bundle first, then writes JSON plus Markdown. The JSON contains only metadata-safe references: case bundle path, object IDs, hashes, provenance refs, reviewed-query refs, safe report paths, and guardrail fields.

## Build All Prompt Packs

```bash
PYENV_VERSION=3.11.3 python tools/build_long_context_prompt_pack.py \
  --all-bundles reports/case_bundles \
  --out-dir reports/long_context
```

This writes one prompt pack per case bundle and an index:

- `reports/long_context/long_context_prompt_pack_index.json`
- `reports/long_context/long_context_prompt_pack_index.md`

## Validate Prompt Pack Or Index

```bash
PYENV_VERSION=3.11.3 python tools/build_long_context_prompt_pack.py \
  --validate reports/long_context/long_context_prompt_pack_index.json
```

Validation fails closed on raw-like fields, provider/model output fields, embedding/vector fields, missing provenance/citation requirements, overclaiming status flags, and unsupported status labels.

## Safe Prompt Templates

Template files live under `docs/prompts/`:

- `long_context_case_review_system_prompt.md`
- `long_context_case_review_user_prompt_template.md`
- `long_context_case_review_output_rubric.md`

These are templates only. They must not include raw transcript text, chunk text, evidence text, provider outputs, model outputs, embeddings, vectors, labels, adjudication rows, training rows, or promotion rows.

Future LLM reviewer prompts must use only supplied bundle references and must require citations to both `object_id` and provenance refs. They must require abstention when provided refs are missing, insufficient, or unsafe.

## Current Readiness Boundary

Required false flags:

- `provider_execution=false`
- `llm_called=false`
- `model_output_present=false`
- `evaluated_model_quality=false`
- `production_claims=false`

Current first20 query rows remain review-pending. Prompt packs can show how a future reviewer would be instructed, but they do not unlock provider execution, model execution, benchmark results, or quality claims.

## Before Real LLM Review

Before any provider-backed long-context review is enabled:

- case bundles must remain metadata-only and validate cleanly
- reviewed-query rows must pass the reviewer gate required by the bakeoff manifest
- generated provider/model artifacts must use approved local paths outside committed artifact classes
- prompts must use fixed bundles and fixed schemas
- reviewer outputs must be validated for citations, abstentions, unsupported conclusions, and hallucination-risk notes
- any quality statement must wait for a completed reviewed evaluation process
