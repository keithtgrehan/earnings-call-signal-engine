# Canonical Repo Hardening Only

## Summary

This branch hardens the canonical `earnings-call-signal-engine` repo without changing `main`, without broadening project scope, and without weakening the deterministic transcript-first path.

## What Changed

- audited the legacy local clone as reference-only and ported one small useful script instead of copying older implementations wholesale
- added a bounded downstream comparison CLI for the fixed media-support casepack
- hardened downstream comparison so rows with missing current `metrics.json` bundles are flagged and excluded from current multimodal accuracy/error summaries instead of crashing or being silently treated as neutral
- tightened media-support/readiness docs and local command guidance
- reduced local-repo confusion after the repo rename by updating stale reference-checkout wording in rerun docs
- refreshed nearby tests, including coverage for missing nonblank artifact paths and one stale multimodal-report test

## Guardrails Preserved

- deterministic transcript-first outputs remain canonical
- support layers remain supporting-only inspection context
- no predictive-edge claims were added
- no statistical-significance claims were added
- no new company cases, UI redesign, or broad framework expansion were introduced

## Legacy Clone Handling

- the legacy local clone was audited for salvage ideas only
- it was not renamed in this pass because it is currently active/dirty and renaming it would risk disrupting local work

## Validation

```bash
pytest -q tests/test_media_support_eval.py tests/test_media_support_comparison.py tests/test_media_support_scripts.py tests/test_multimodal_support.py
PYTHONPATH=src python3 scripts/check_media_support_readiness.py
PYTHONPATH=src python3 scripts/compare_multimodal_support_slice.py --help
PYTHONPATH=src python3 scripts/compare_multimodal_support_slice.py
git diff --check
```

Results:

- `16 passed in 2.87s`
- readiness script completed and wrote `outputs/media_support_eval/media_support_readiness.json`
- comparison script completed and wrote `outputs/media_support_eval/downstream_decision_comparison.json` plus `downstream_decision_comparison_rows.csv`
- whitespace / patch hygiene checks are clean

## Reviewer Notes

- This is canonical-repo hardening only.
- The most important behavior change is the new explicit handling of missing downstream artifact bundles: comparison output now reports coverage and excludes unavailable current bundles from current multimodal summary metrics.
- The old audio source manifest still references legacy-local cache files; that remains documented truthfully rather than being rewritten speculatively.
