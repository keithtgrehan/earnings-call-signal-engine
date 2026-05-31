# First100 Manual Adjudication Guide

This guide supports manual review of the first100 metadata-only signal candidates. It does not create gold labels, promotion records, training data, or raw evidence artifacts.

## Purpose

The first100 adjudication pass lets a human reviewer inspect machine candidates from `data/review/staging/first100_signal_candidates.jsonl` using the review packets in `data/review/packets/first100_batch_*.md`. The reviewer records a metadata-only decision in `data/review/staging/first100_adjudication_draft.jsonl`.

The draft is reviewer input only. It remains separate from gold labels and cannot make training or promotion ready by itself.

## Why The Draft Starts Empty

`data/review/staging/first100_adjudication_draft.jsonl` starts empty because every JSONL row is treated as a human-reviewed adjudication row. Blank row stubs would look like incomplete decisions and would fail validation.

An empty draft means the workflow is initialized but `NOT_READY`: manual review is still required, promotion remains blocked, and training remains blocked.

## How To Fill Rows

Add one JSON object per line only after a human reviewer has inspected the candidate and the approved Desktop source material. Use `docs/review/first100_adjudication_row_template.json` as a documentation-only shape reference, then copy real identifiers and hashes from the packet or candidate file.

No raw transcript text belongs in the draft. Do not paste quotes, snippets, source excerpts, audio text, ASR text, or chunk text.

## Required JSONL Fields

- `candidate_id`: exact candidate id from the review packet.
- `case_id`: exact case id from the review packet.
- `ticker`: exact ticker from the review packet.
- `fiscal_period`: exact fiscal period from the review packet.
- `suggested_label`: machine suggestion copied as context only, or `MACHINE CANDIDATE ONLY`.
- `adjudicated_label`: one valid label chosen by the human reviewer.
- `review_status`: `adjudicated`.
- `gold_status`: `not_gold`.
- `reviewer`: stable reviewer id with at least three letters/numbers.
- `rationale`: short reason without raw transcript text.
- `source_file`: source path from the packet or candidate metadata.
- `source_sha256`: source hash from the packet or candidate metadata.
- `normalized_transcript_hash`: normalized transcript hash from the packet or candidate metadata.
- `text_hash`: candidate text hash from the packet or candidate metadata.
- `provenance_hash`: provenance hash from the packet or candidate metadata.
- `evidence_object_id`: evidence object id when available.
- `chunk_id`: chunk id when available.
- `promotion_decision`: `not_requested`.
- `training_export_requested`: `false`.
- `training_allowed`: `false`.
- `explicit_training_rights_ref`: empty string.

At least one of `evidence_object_id` or `chunk_id` must be present.

## Valid Label Values

- `guidance_revision`
- `guidance_statement`
- `analyst_pressure`
- `management_hedging`
- `uncertainty`
- `reassurance`
- `answer_shift`
- `neutral/no_signal`
- `reject_candidate`
- `needs_source_review`
- `needs_adjudication`

## Valid Rejection Reasons

Use `rejection_reason` when `adjudicated_label` is `reject_candidate` or `needs_source_review`. Keep it brief and metadata-only.

- `safe_harbor_or_non_gaap`
- `operator_or_vendor_disclaimer`
- `generic_optimism`
- `historical_only`
- `analyst_only_unpaired_question`
- `unsupported_guidance_comparator`
- `wrong_case_or_period`
- `missing_source_or_hash`
- `duplicate_candidate`
- `source_needs_review`
- `not_a_signal`

## Evidence Text Requirements

No raw transcript body, quote, snippet, ASR text, audio-derived text, or chunk text may be committed in the adjudication draft. Evidence is represented by IDs and hashes only:

- `evidence_object_id` or `chunk_id`
- `source_sha256`
- `normalized_transcript_hash`
- `text_hash`
- `provenance_hash`

The reviewer may inspect approved source material locally, but the JSONL row must stay metadata-only.

## What Must Never Be Guessed

Do not guess:

- `adjudicated_label`
- `candidate_id`
- `case_id`
- `ticker`
- `fiscal_period`
- `source_file`
- `source_sha256`
- `normalized_transcript_hash`
- `text_hash`
- `provenance_hash`
- `evidence_object_id`
- `chunk_id`
- `reviewer`
- training rights
- promotion readiness

If source material, identifiers, or hashes are unclear, use `needs_source_review` or `needs_adjudication` and explain the issue without raw text.

## Keep Promotion And Training Blocked

Promotion remains blocked until a separate promotion manifest exists and passes `tools/validate_first100_promotion_manifest.py`.

Training remains blocked until there are at least 100 valid adjudicated labels, provenance is complete, promotion gates pass, and explicit training rights are configured. The adjudication draft must keep:

- `gold_status=not_gold`
- `promotion_decision=not_requested`
- `training_export_requested=false`
- `training_allowed=false`
- `explicit_training_rights_ref=""`

Run the validation sequence after editing:

```bash
python3 tools/validate_first100_adjudication_file.py data/review/staging/first100_adjudication_draft.jsonl
python3 tools/validate_first100_promotion_manifest.py --manifest data/review/staging/first100_promotion_manifest.jsonl
python3 tools/build_review_readiness_dashboard.py
```

Expected status before completed human review: `NOT_READY`, `promotion_ready=false`, `training_ready=false`.
