# Reference Case Standardization Verification

## What Was Checked

- `docs/reference_case_standard.md`
- `docs/reference_case_standardization_summary.md`
- `docs/reference_case_standardization_pr_notes.md`
- `docs/reference_case_standardization_audit.md`
- `docs/repo_hygiene_map.md`
- `scripts/validate_reference_case_package.py`
- `src/earnings_call_sentiment/reference_case_standard.py`
- touched reviewer-language and support-layer wording paths from this branch diff
- Netflix reference package validation against the branch validator

## Issues Found

- The reference-case validator did not actually enforce the per-moment `caveat` requirement even though the standard document described per-moment reviewer caveat text as part of the package bar.
- No additional reviewer-language overstatement was found in the manually inspected branch-specific docs and touched support-layer wording paths after this pass.

## What Was Corrected

- Tightened `validate_reference_case_package()` so panel payloads now fail if any moment row is missing a non-empty `caveat`.
- Added a focused regression test covering the missing-caveat failure path.

## What Remains Acceptable But Worth Reviewer Attention

- The validator is still intentionally a reviewed-package validator, not a full surrounding-doc validator. The docs themselves still need human review.
- Historical repo areas outside this bounded branch still contain legacy field names such as `confidence` and `support_direction`; this pass did not broaden into a repo-wide schema rewrite.
- Netflix remains the practical gold reference, but it is still a fixed case pack rather than a generalized framework.

## Exact Commands Run

```bash
git diff --unified=40 main...HEAD -- src/earnings_call_sentiment/multimodal_support.py src/earnings_call_sentiment/media_support_comparison.py src/earnings_call_sentiment/audio/summary.py src/earnings_call_sentiment/audio/segment_aggregate.py src/earnings_call_sentiment/visual/summary.py src/earnings_call_sentiment/visual/segment_aggregate.py scripts/check_media_support_readiness.py scripts/compare_multimodal_support_slice.py
git diff --unified=20 main...HEAD -- README.md data/audio_signal_eval/README.md data/media_support_eval/README.md data/multimodal_signal_eval/README.md docs/april-2-demo-side-by-side.md docs/current-status.md docs/demo-path.md docs/msft-ambiguity-explainer.md docs/multimodal-data-plan.md docs/nlp-rerun-plan.md docs/overnight_run_log_20260310.md
PYTHONPATH=src pytest -q tests/test_reference_case_standard.py
PYTHONPATH=src python3 scripts/validate_reference_case_package.py --package-dir "/Users/keith/Documents/New project/main-demo-wt/data/demo_cases/netflix_q1_2022/demo/multimodal" --prefix netflix
git diff --check
```

## Tests Run And Results

- `PYTHONPATH=src pytest -q tests/test_reference_case_standard.py`
  - result: `5 passed`
- `PYTHONPATH=src python3 scripts/validate_reference_case_package.py --package-dir "/Users/keith/Documents/New project/main-demo-wt/data/demo_cases/netflix_q1_2022/demo/multimodal" --prefix netflix`
  - result: `valid: true`
- `git diff --check`
  - result: clean at verification time
