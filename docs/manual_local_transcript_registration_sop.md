# Manual-Local Transcript Registration SOP

Status: path/hash registration only. Do not copy transcript, audio, video, or slide bodies into the repository.

## Approved Folders

- `/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/transcripts/`
- `/Users/keith/Desktop/Signal Engine 2.0 Earning Calls/`
- `/Users/keith/Documents/New project/earnings-call-signal-engine-support-qa/data/corpus/manual_cases/`

## Workflow

1. Place locally held transcript files in an approved folder.
2. Run `make discover-approved-local-transcripts`.
3. Run `make build-manual-local-batch`.
4. Edit `data/review/staging/manual_local_batch_candidate.csv` with source URL and rights context.
5. Keep `commit_allowed=false` and `training_allowed=false` unless explicit rights documentation supports otherwise.
6. Run `python scripts/register_manual_local_batch.py --batch data/review/staging/manual_local_batch_candidate.csv`.
7. Run `make manual-local-registration-check`.

## Guardrails

- Unknown or restricted rights cannot enable eval, training, or commit permissions.
- PDFs are registered as path/hash references only; no OCR is run.
- Transcript bodies are not parsed during discovery or registration.
- Manual-local records store `source_path_ref`, `source_sha256`, flags, and provenance only.
- Canonical `data/gold/gold_labels.jsonl` is never edited by this workflow.

Training remains `NOT_READY` until at least 100 valid adjudicated labels pass validation.
