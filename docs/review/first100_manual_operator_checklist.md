# First100 Manual Operator Checklist

This checklist is for local human review of first100 adjudication rows. It does not create labels, gold labels, promotion rows, training data, or raw artifacts.

## Manual Workflow

1. Open the reviewer packet:
   `reports/review/first100_reviewer_packet.md`
2. Inspect candidate metadata only:
   `data/review/staging/first100_signal_candidates.jsonl`
3. Open the documentation-only row shape:
   `docs/review/first100_adjudication_row_template.json`
4. Inspect the approved local Desktop source material referenced by the candidate metadata when needed.
5. Manually add exactly one JSON object line to:
   `data/review/staging/first100_adjudication_draft.jsonl`
6. Run the staging validator.
7. Fix validation errors without changing semantic reviewer intent.
8. Repeat one candidate at a time.
9. Rebuild the review dashboard after each review session.

## Do Not Paste Raw Text

Before saving a draft row, confirm all of these are true:

- No transcript quotes are pasted.
- No source snippets are pasted.
- No chunk text is pasted.
- No ASR or audio-derived text is pasted.
- No PDF/body text is pasted.
- No provider raw payload is pasted.
- No `quote`, `snippet`, `raw_text`, `evidence_text`, or `final_evidence_text` field is present.
- Evidence is represented only by IDs and hashes.

## Valid Row Before Commit

Before committing an edited draft, each non-empty JSONL row must satisfy:

- `candidate_id` exists in `data/review/staging/first100_signal_candidates.jsonl`.
- `case_id`, `ticker`, and `fiscal_period` match the candidate metadata.
- `adjudicated_label` is one allowed label from the manual guide.
- `review_status` is `adjudicated`.
- `gold_status` is `not_gold`.
- `promotion_decision` is absent or `not_requested`.
- `training_export_requested` is absent or `false`.
- `training_allowed` is absent or `false`.
- `explicit_training_rights_ref` is absent or empty.
- `reviewer` is a stable non-empty reviewer id.
- `reviewed_at` is UTC ISO-8601 with trailing `Z`, for example `2026-05-31T12:00:00Z`.
- `rationale` is metadata-only and contains no raw source text.
- `source_sha256`, `normalized_transcript_hash`, `text_hash`, and `provenance_hash` are present.
- At least one of `evidence_object_id` or `chunk_id` is present.
- `rejection_reason` is present when `adjudicated_label` is `reject_candidate` or `needs_source_review`.

## Blocked Until Human Review Complete

The initialized empty draft is expected to remain `NOT_READY` until humans add and validate rows. The workflow remains blocked unless later gates explicitly pass:

- `promotion_ready=false`
- `training_ready=false`
- `promotion_manifest_status=NOT_READY`
- no gold labels created
- no promotion rows created
- no training data created

Validation of the staging draft means only that the draft is well-formed reviewer input. It does not promote labels, create gold labels, or authorize training.

## Local Commands

Validate the draft:

```bash
PYENV_VERSION=3.11.3 python tools/validate_first100_adjudication.py --draft data/review/staging/first100_adjudication_draft.jsonl --mode staging
```

Rebuild the reviewer packet:

```bash
PYENV_VERSION=3.11.3 python tools/build_first100_reviewer_packet.py
```

Rebuild the review dashboard:

```bash
PYENV_VERSION=3.11.3 python tools/build_review_readiness_dashboard.py
```

Check changed paths for restricted artifacts:

```bash
changed_paths="$(git diff --name-only main...HEAD)"
test -z "$changed_paths" || PYENV_VERSION=3.11.3 python scripts/check_restricted_artifacts.py $changed_paths
```

Check for forbidden raw or generated artifact paths:

```bash
git diff --name-only main...HEAD | grep -Ei '(\.pdf$|\.mp3$|\.wav$|\.m4a$|\.mp4$|\.mov$|\.parquet$|\.pkl$|\.joblib$|\.sqlite$|\.db$|embedding|vector|raw|asr|audio|model|provider|training)' && echo "REVIEW REQUIRED" || true
```
