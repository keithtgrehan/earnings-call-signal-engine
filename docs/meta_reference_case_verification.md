# Meta Reference Case Verification

## What Was Checked

- `docs/reference_case_standard.md`
- `docs/meta_multimodal_asset_audit.md`
- `docs/meta_multimodal_evidence_panel.md`
- `docs/meta_multimodal_panel_summary.md`
- `docs/meta_multimodal_handoff_summary.md`
- `docs/meta_multimodal_pr_description.md`
- `data/demo_cases/meta_q3_2022/demo/multimodal/meta_multimodal_panel.json`
- `data/demo_cases/meta_q3_2022/demo/multimodal/meta_multimodal_panel.md`
- `data/demo_cases/meta_q3_2022/demo/multimodal/meta_model_comparison.json`
- `data/demo_cases/meta_q3_2022/demo/multimodal/meta_disagreement_hotspots.json`
- `data/demo_cases/meta_q3_2022/demo/multimodal/meta_pressure_moments_panel.json`
- `data/demo_cases/meta_q3_2022/demo/multimodal/meta_supporting_only_caveats.json`
- `data/demo_cases/meta_q3_2022/demo/multimodal/meta_visual_support_skipped.json`
- `scripts/build_meta_multimodal_panel.py`
- `scripts/validate_reference_case_package.py`
- `src/earnings_call_sentiment/meta_multimodal_panel.py`
- `src/earnings_call_sentiment/reference_case_standard.py`
- `src/earnings_call_sentiment/nlp_sidecars/evaluate.py`
- `tests/test_meta_multimodal_panel.py`
- `tests/test_nlp_sidecars_evaluate.py`
- `tests/test_reference_case_standard.py`

## Issues Found

- The branch-local reference-case validator still lagged the shared standardization branch and did not enforce legacy `nlp_sidecars` caveat coverage when a model-comparison artifact exists.
- Meta pressure-panel rows were otherwise structurally aligned with Netflix, but they still lacked `why_selected`.
- No new Meta artifact truthfulness issue was found in this pass. The visual skip remained explicit and consistent across the asset audit, skip artifact, panel JSON, panel markdown, and handoff summary.

## What Was Corrected

- Mirrored the validator hardening on this branch so the local validator now catches the same legacy `nlp_sidecars` caveat gap as the shared standardization branch.
- Added the matching regression to `tests/test_reference_case_standard.py`.
- Added `why_selected` to Meta pressure-panel rows and updated the persisted pressure artifact for cleaner Netflix/Meta parity.
- Revalidated the final Meta package after the bounded fixes.

## What Remains Acceptable But Worth Reviewer Attention

- The Meta pack is still bounded to `12` curated moments and only `2` aligned main-call audio windows.
- The final persisted visual layer remains intentionally skipped, even though a local MP4 exists, because earlier heuristic full-video attempts exceeded the reviewer-safe runtime cap.
- Follow-up, release, and presentation moments still do not have timed main-call video windows.
- The final sidecar comparison remains limited to `finbert_tone` and `financial_roberta`.
- Netflix still uses the legacy grouped caveat payload shape while Meta uses the flat id-list layout; both remain reviewer-safe under the shared validator.

## Exact Commands Run

```bash
PYTHONPATH=src pytest -q tests/test_meta_multimodal_panel.py tests/test_nlp_sidecars_evaluate.py tests/test_reference_case_standard.py
PYTHONPATH=src python3 scripts/validate_reference_case_package.py --package-dir data/demo_cases/meta_q3_2022/demo/multimodal --prefix meta
PYTHONPATH=src pytest -q tests/test_meta_multimodal_panel.py
git diff --check
```

## Tests Run And Results

- `PYTHONPATH=src pytest -q tests/test_meta_multimodal_panel.py tests/test_nlp_sidecars_evaluate.py tests/test_reference_case_standard.py`
  - result: `20 passed`
- `PYTHONPATH=src python3 scripts/validate_reference_case_package.py --package-dir data/demo_cases/meta_q3_2022/demo/multimodal --prefix meta`
  - result: `valid: true`
- `PYTHONPATH=src pytest -q tests/test_meta_multimodal_panel.py`
  - result: `12 passed`
- `git diff --check`
  - result: clean after the verification edits in this pass

## Branch Status

- branch: `feat/meta-q3-2022-reference-case`
- worktree: `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-meta-reference-case`
- verification scope: bounded validator/parity/doc updates only
