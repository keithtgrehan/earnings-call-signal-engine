# Long-Context Review Output Import Process

Status: `long_context_review_output_validation_only`.

This process validates sanitized long-context reviewer-output candidates created outside the default repo workflow. It checks structure, bundle refs, prompt-pack refs, citations, abstentions, and claim safety. It does not call LLMs, run providers, score reviewers, create labels, or make model-quality claims.

## Validate One Candidate

```bash
PYENV_VERSION=3.11.3 python tools/validate_long_context_review_output.py \
  --review-output data/retrieval/long_context_review_output.sample_abstain.json \
  --prompt-pack reports/long_context/HD_2025_Q4.prompt_pack.json \
  --bundle reports/case_bundles/HD_2025_Q4.case_review_bundle.json \
  --out reports/long_context/HD_2025_Q4.review_output_validation.md \
  --json-out reports/long_context/HD_2025_Q4.review_output_validation.json
```

The validator accepts JSON objects, JSON arrays of objects, and JSONL objects. Input paths for case bundle and prompt pack files are resolved case-insensitively for the filename, so the command above can point at `HD_2025_Q4` while the committed files remain lowercase.

## Validate Sample Batch

```bash
PYENV_VERSION=3.11.3 python tools/validate_long_context_review_output.py \
  --all-samples data/retrieval \
  --prompt-pack-dir reports/long_context \
  --bundle-dir reports/case_bundles \
  --out-dir reports/long_context/review_output_validations
```

Batch mode validates committed `long_context_review_output.sample_*.json` and `.jsonl` files only. It writes one validation report per sample plus:

- `reports/long_context/review_output_validations/long_context_review_output_validation_index.json`
- `reports/long_context/review_output_validations/long_context_review_output_validation_index.md`

## Required Candidate Shape

Each candidate must include metadata-safe fields only:

- `case_id`
- `reviewer_model_slot`
- `reviewed_bundle_id`
- `source_prompt_pack_id`
- `summary`
- `conclusions`
- `cited_object_refs`
- `cited_provenance_refs`
- `detected_issues`
- `uncertainty_flags`
- `extraction_disagreements`
- `hallucination_risk_notes`
- `reviewer_confidence`
- `abstentions`
- `cannot_answer_reasons`

Substantive conclusions must cite at least one `object_id` and one provenance ref from the case bundle. Abstentions are valid when explicit and accompanied by `cannot_answer_reasons`.

## Forbidden Content

Do not include:

- raw transcript text
- raw ASR/audio text
- raw chunk text
- raw evidence text
- provider raw responses
- model raw responses
- chain-of-thought, scratchpad, trace, or hidden reasoning fields
- embeddings, vectors, vector DBs, or index artifacts
- labels, gold labels, adjudication rows, training rows, or promotion rows
- trading, alpha, unsupported statistical, production RAG, or model-quality claims

## Status Boundary

Validation reports must keep these fields false:

- `provider_execution=false`
- `llm_called_by_this_tool=false`
- `model_output_present=false`
- `evaluated_model_quality=false`
- `benchmark_complete=false`
- `production_claims=false`

Passing validation means the candidate is structurally safe to inspect. It does not mean the reviewer is correct, useful, benchmarked, or ready for production use.

## Before Scoring Long-Context Reviewers

Future scoring requires:

- reviewed query rows that pass the benchmark-readiness gate
- fixed prompt packs and fixed case bundles
- a provider execution manifest that keeps generated artifacts outside committed restricted paths
- citation quality scoring
- faithfulness scoring
- hallucination-risk review
- a clear rule for abstention correctness
