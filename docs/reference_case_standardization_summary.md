# Reference Case Standardization Summary

## What Was Standardized

- standardized honest downstream comparison behavior so missing current bundles are flagged and excluded rather than silently treated as comparable
- standardized readiness output so it now reports target-comparable downstream coverage explicitly
- added a small reusable reference-case standard module plus validator CLI
- documented the reusable artifact/doc/caveat bar for future bounded case packages
- tightened reviewer-facing wording in the highest-signal support-layer docs and summary notes

## What Wording Was Tightened

- demo-path language that implied audio was simply "supportive"
- nearby Microsoft demo/explainer wording that treated same-direction audio context like stronger validation than intended
- planning/readiness language that used `confidence` where `usability` or `quality-gated` was more accurate
- audio/visual note strings that implied stronger support than intended
- rerun-path and repo-path wording that still pointed at stale feature-worktree assumptions

## What Helpers / Validators Were Added

- `src/earnings_call_sentiment/reference_case_standard.py`
- `scripts/validate_reference_case_package.py`
- `scripts/compare_multimodal_support_slice.py`

The validator accepts both:

- the flat-id caveat format recommended for future packages
- the existing Netflix reference-case layout already committed on the reference branch

## What Tests Were Added / Updated

- added:
  - `tests/test_reference_case_standard.py`
  - `tests/test_media_support_scripts.py`
- updated:
  - `tests/test_media_support_comparison.py`
  - `tests/test_multimodal_support.py`
  - `tests/test_audio_behavior.py`
  - `tests/test_visual_behavior.py`

## What Was Deliberately Not Changed

- did not port the full Netflix multimodal bundle onto `main`
- did not rewrite historical committed artifacts wholesale
- did not redesign the UI
- did not add new model families or new cross-company framework scope
- did not weaken transcript-first deterministic outputs

## Exact Commands Run

```bash
PYTHONPATH=src pytest -q tests/test_media_support_eval.py tests/test_media_support_comparison.py tests/test_media_support_scripts.py tests/test_multimodal_support.py tests/test_audio_behavior.py tests/test_visual_behavior.py tests/test_reference_case_standard.py
PYTHONPATH=src python3 scripts/check_media_support_readiness.py
PYTHONPATH=src python3 scripts/compare_multimodal_support_slice.py
PYTHONPATH=src python3 scripts/validate_reference_case_package.py --help
PYTHONPATH=src python3 scripts/validate_reference_case_package.py --package-dir "/Users/keith/Documents/New project/main-demo-wt/data/demo_cases/netflix_q1_2022/demo/multimodal" --prefix netflix
git diff --check
```

Read-only Netflix reference validation in the existing reference worktree:

```bash
PYTHONPATH=src pytest -q tests/test_netflix_multimodal_panel.py tests/test_nlp_sidecars_config.py tests/test_nlp_sidecars_evaluate.py tests/test_nlp_sidecars_io.py tests/test_nlp_sidecars_runner.py tests/test_run_nlp_sidecars.py
PYTHONPATH=src python3 scripts/build_netflix_multimodal_panel.py --help
```

## Recommended Next Step Before Another Case Port

Use `feat/netflix-reference-case-hardening` plus [reference_case_standard.md](reference_case_standard.md) as the quality bar, and validate the next bounded package with `scripts/validate_reference_case_package.py` before treating it as demo/reviewer ready.
