# Reference Case Standardization Verification

## What Was Checked

- `docs/reference_case_standard.md`
- `docs/reference_case_standardization_summary.md`
- `docs/reference_case_standardization_pr_notes.md`
- `docs/reference_case_standardization_audit.md`
- `docs/reference_case_parity_check.md`
- `docs/repo_hygiene_map.md`
- `scripts/validate_reference_case_package.py`
- `src/earnings_call_sentiment/reference_case_standard.py`
- touched reviewer-language and support-layer wording paths from this branch diff
- Netflix and Meta reference package validation against the branch validator

## Issues Found

- `docs/repo_hygiene_map.md` no longer matched the active canonical worktree lineup. It omitted the clean Meta and retrieval worktrees and described the Netflix reference worktree as effectively read-only even though a bounded reviewer-safety fix pass may need to land there.
- No new validator enforcement defect was found in this pass. The branch validator still accepts the current Netflix and Meta packages and still enforces the package-level caveat and visual-status rules it claims to enforce.

## What Was Corrected

- Updated `docs/repo_hygiene_map.md` so it now starts with a fresh `git worktree list` check, records the active clean worktrees for the current bounded reference-case branches, and keeps Netflix guidance accurate for bounded review/fix work when that worktree is clean.
- Updated `docs/reference_case_parity_check.md` to capture the current cross-case parity review, including the Netflix handoff-summary correction made in this verification pass.

## What Remains Acceptable But Worth Reviewer Attention

- The validator is still intentionally a reviewed-package validator, not a full surrounding-doc validator. The docs themselves still need human review.
- Historical repo areas outside this bounded branch still contain legacy field names such as `confidence` and `support_direction`; this pass did not broaden into a repo-wide schema rewrite.
- Netflix and Meta still differ intentionally in a few bounded ways:
  - Netflix keeps a legacy grouped caveat payload while Meta uses the flat id-list caveat payload.
  - Netflix persists a heuristic-fallback visual artifact while Meta persists a case-level visual skip artifact.
  - The handoff filenames differ even though the handoff content is now aligned more closely.

## Exact Commands Run

```bash
git worktree list
PYTHONPATH=src pytest -q tests/test_reference_case_standard.py
PYTHONPATH=src python3 scripts/validate_reference_case_package.py --package-dir "/Users/keith/Documents/New project/main-demo-wt/data/demo_cases/netflix_q1_2022/demo/multimodal" --prefix netflix
PYTHONPATH=src python3 scripts/validate_reference_case_package.py --package-dir "/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-meta-reference-case/data/demo_cases/meta_q3_2022/demo/multimodal" --prefix meta
git diff --check
```

## Tests Run And Results

- `PYTHONPATH=src pytest -q tests/test_reference_case_standard.py`
  - result: `5 passed`
- `PYTHONPATH=src python3 scripts/validate_reference_case_package.py --package-dir "/Users/keith/Documents/New project/main-demo-wt/data/demo_cases/netflix_q1_2022/demo/multimodal" --prefix netflix`
  - result: `valid: true`
- `PYTHONPATH=src python3 scripts/validate_reference_case_package.py --package-dir "/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-meta-reference-case/data/demo_cases/meta_q3_2022/demo/multimodal" --prefix meta`
  - result: `valid: true`
- `git diff --check`
  - result: clean at verification time
