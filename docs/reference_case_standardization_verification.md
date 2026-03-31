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
- `tests/test_reference_case_standard.py`
- live Netflix and Meta reference packages against the branch validator

## Issues Found

- The written standard says a legacy grouped caveat payload must include `nlp_sidecars` when a model-comparison artifact is present, but the branch validator did not enforce that condition.
- No new doc-language defect required a code change in this pass. The highest-signal standard docs still keep transcript-first and supporting-only boundaries explicit.

## What Was Corrected

- Added `<prefix>_model_comparison.json` detection to the shared reference-case path map.
- Hardened the validator so legacy grouped caveat payloads now fail when a model-comparison artifact exists but `nlp_sidecars` is missing.
- Added a focused regression covering that validator path.
- Revalidated the current Netflix and Meta packages after the hardening change.

## What Remains Acceptable But Worth Reviewer Attention

- The validator is still intentionally a reviewed-package validator, not a full surrounding-doc validator.
- Historical repo areas outside this bounded branch still contain legacy field names such as `confidence` and `support_direction`; this pass did not broaden into a repo-wide schema rewrite.
- Netflix and Meta still differ intentionally in a few bounded ways:
  - Netflix keeps a legacy grouped caveat payload while Meta uses the flat id-list caveat payload.
  - Netflix persists a heuristic-fallback visual artifact while Meta persists a case-level visual skip artifact.
  - Netflix still exposes `cleaner_sidecar_examples` while Meta exposes `strong_supporting_context_moments`.

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
  - result: `6 passed`
- `PYTHONPATH=src python3 scripts/validate_reference_case_package.py --package-dir "/Users/keith/Documents/New project/main-demo-wt/data/demo_cases/netflix_q1_2022/demo/multimodal" --prefix netflix`
  - result: `valid: true`
- `PYTHONPATH=src python3 scripts/validate_reference_case_package.py --package-dir "/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-meta-reference-case/data/demo_cases/meta_q3_2022/demo/multimodal" --prefix meta`
  - result: `valid: true`
- `git diff --check`
  - result: clean after the verification edits in this pass

## Branch Status

- branch: `chore/reference-case-standardization`
- worktree: `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-reference-standardization`
- verification scope: bounded validator/test/doc updates only
