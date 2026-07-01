# Post-PR63 Control-Room Status

- Branch: `codex/post-pr63-control-room-audit-review-accelerator`
- Base commit: `2116cff6b2829b88e2268a3eb95999d6ec05b2f0` (`Add first100 adjudication draft scaffold (#63)`)
- Local sync: `origin/main` fetched and local `main` fast-forwarded to `2116cff`
- PR #63 merge visible on `origin/main`: true
- Baseline working tree after sync and before branch edits: clean
- Current branch changes: review-assist tooling, generated weak-assist reports, validation/report docs
- Raw transcript/audio/ASR/chunk/model/vector/provider artifacts committed by this branch: false
- Final adjudication automated: false
- Gold labels created: 0
- Promotion candidates created: 0
- Training performed: false

## Merged PRs #59-#63

- #59 `Add EarningsCall provider integration and first30 extraction review path`: merged `2026-05-30T23:28:58Z`, commit `cefe1594ae457b015b1a848eb23a91dd21298012`.
- #60 `Add first100 review candidate expansion and training readiness bridge`: merged `2026-05-30T23:50:48Z`, commit `36b27b6618032cb1f0fbc99b6c6a0963bc6cfc8e`.
- #61 `Codex/first100 review candidate expansion training readiness`: merged `2026-05-31T00:03:04Z`, commit `4a529789370ec883f26f35e7eea6de5354c03879`.
- #62 `Harden first100 adjudication review workflow`: merged `2026-05-31T00:06:45Z`, commit `38b661b9c4656ca42a7dfb4399a0baa17e482255`.
- #63 `Add first100 adjudication draft scaffold`: merged `2026-05-31T10:42:32Z`, commit `2116cff6b2829b88e2268a3eb95999d6ec05b2f0`.

## PR #50 Status

- PR #50 `Add transcript source discovery adapters and normalized transcript contracts` is already `CLOSED`.
- GitHub reports it as `CONFLICTING` against current `main`.
- Several PR #50 file paths are not present on current `main`, but the later #51-#63 path now covers the active provider, asset-resolution, first100 review, adjudication-safety, and training-readiness workflow.
- Recommendation: leave PR #50 closed. Treat it as partially superseded and stale; only perform a separate salvage review if Keith explicitly wants those old discovery-adapter ideas reconsidered.

## Current Counts

- Registered transcripts: 31
- Normalized transcripts: 31
- Chunks: 468
- Evidence objects: 44
- Retrieval objects: 512
- First100 candidates: 100
- Candidates by label: `{"analyst_pressure": 7, "guidance_revision": 2, "guidance_statement": 20, "management_hedging": 2, "neutral/no_signal": 67, "uncertainty": 2}`
- Review packets generated: 5
- Calibration rows: 24
- Adjudicated rows: 0
- Valid adjudicated labels: 0
- Promotion candidates: 0
- Training ready: false

## Public Model Assist Status

- Registry: `data/review/public_model_assist_registry.example.yml`
- Registry validation: valid
- Registered public/local assets: 5
- License-cleared weak-review-assist assets: 0
- Training-enabled assets: 0
- Downloads performed: false
- Raw data committed: false
- Model weights committed: false
- Public/local model outputs used: false
- Weak assist method: `metadata_rule_heuristic`
- Weak assist rows generated: 100
- Weak assist CSV: `reports/review/first100_weak_model_assist.csv`
- Review accelerator CSV: `reports/review/first100_review_accelerator.csv`
- Final adjudication automated by weak assist: false

## Blockers

- Human adjudication is still missing: valid adjudicated labels are `0/100`.
- Promotion manifest is not ready because human adjudication has not been supplied.
- Explicit training rights are not configured.
- No public model, dataset, or lexicon is currently license-cleared for weak review assistance in the registry.
- Unknown-license and blocked assets fail closed.

## Validation Results

- `git status --short`: clean before implementation; branch now has expected review-assist changes pending commit.
- `python -m py_compile $(git ls-files '*.py')`: passed.
- `pytest -q`: passed, `789 passed in 59.65s`.
- Initial baseline `pytest -q` failure before this branch fix: `tests/test_no_raw_audio_committed.py` scanned local `.venv` package WAV fixtures; the test now checks git-tracked files, matching the "committed artifact" guardrail.
- `pytest -q tests/test_no_raw_audio_committed.py tests/test_public_model_assist_registry.py tests/test_first100_weak_model_assist.py`: passed, `7 passed`.
- `python tools/validate_first100_adjudication_file.py data/review/staging/first100_adjudication_draft.jsonl`: expected `NOT_READY`, `adjudicated_rows=0`, `gold_labels_created=0`.
- `python tools/validate_first100_promotion_manifest.py --manifest data/review/staging/first100_promotion_manifest.jsonl`: expected `NOT_READY`, manifest missing, `gold_promoted=0`.
- `python tools/report_first100_training_readiness.py`: `REVIEW_READY`, `training_performed=false`, blockers are missing adjudication, missing training rights, missing promotion manifest.
- `python tools/build_review_readiness_dashboard.py`: reports 100 candidates, 0 adjudicated rows, 0 promotion candidates, raw text committed false.
- `python tools/validate_public_model_assist_registry.py data/review/public_model_assist_registry.example.yml`: passed, 5 assets, no cleared weak-assist assets, no downloads, no raw/model files committed.
- `python tools/build_first100_weak_model_assist.py`: passed, 100 metadata-only weak-assist rows, 0 disagreements, no raw text used or returned.
- `python tools/build_first100_review_spreadsheet.py`: passed, 100 manual-review rows.
- `make validate-public-model-assist-registry first100-weak-model-assist first100-review-accelerator`: passed.
- `python scripts/check_restricted_artifacts.py --dry-run`: passed, 14 staged path(s) checked.
- `git diff --check`: passed.
- `git diff --cached --check`: passed.

## Next Manual Action

Keith should open `reports/review/first100_review_accelerator.csv` and the matching packet files, review the high-priority and medium-priority rows first, and write human decisions only into a separate adjudication draft when ready. The weak-assist CSV is reviewer support only and must not be copied as final adjudication without human review.
