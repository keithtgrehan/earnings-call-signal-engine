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
- `data/demo_cases/meta_q3_2022/demo/multimodal/meta_supporting_only_caveats.json`
- `data/demo_cases/meta_q3_2022/demo/multimodal/meta_visual_support_skipped.json`
- `scripts/build_meta_multimodal_panel.py`
- `src/earnings_call_sentiment/meta_multimodal_panel.py`
- `src/earnings_call_sentiment/nlp_sidecars/evaluate.py`
- `tests/test_meta_multimodal_panel.py`
- `tests/test_nlp_sidecars_evaluate.py`

## Mismatches Vs The Standard That Were Found

- The final case-level visual skip was honest in `meta_visual_support_skipped.json`, but some downstream panel surfaces flattened that into generic per-moment `unavailable` language instead of preserving the case-level skip.
- The shared reference-case validator still accepted panel rows with no per-moment `caveat`, which was weaker than the stated standard.
- The Meta panel already had the top-8 showcase embedded per row, but it did not expose an explicit top-8 id list or panel-level canonical/supporting-only flags, which made parity checking less direct than it needed to be.

## What Was Corrected

- Propagated the case-level visual skip into the Meta panel JSON and reviewer-note surfaces for timestamped main-call moments, while keeping untimed moments explicitly unavailable.
- Added explicit `top_8_showcase_moment_ids`, panel-level canonical/supporting-only flags, and panel-level visual status fields to the Meta panel payload.
- Mirrored the validator hardening so the Meta branch now also rejects panel packages with missing per-moment caveats.
- Regenerated the persisted Meta review bundle after the fix so the JSON and markdown surfaces match the skip behavior.

## What Remains Acceptable But Should Be Called Out In Review

- The Meta pack is still bounded to `12` curated moments and only `2` aligned main-call audio windows.
- The final persisted visual layer is intentionally skipped, even though a local MP4 exists, because earlier heuristic full-video attempts exceeded the reviewer-safe runtime cap.
- Follow-up, release, and presentation moments still do not have timed main-call video windows.
- The final sidecar comparison remains limited to `finbert_tone` and `financial_roberta`.
- Netflix still uses the legacy grouped caveat payload shape while Meta uses the flat id list; both are accepted by the validator and are reviewer-safe.

## Exact Commands Run

```bash
PYTHONPATH=src pytest -q tests/test_reference_case_standard.py tests/test_meta_multimodal_panel.py tests/test_nlp_sidecars_evaluate.py
PYTHONPATH=src python3 scripts/build_meta_multimodal_panel.py --device auto --visual-sample-fps 0 --models finbert_tone financial_roberta
PYTHONPATH=src python3 scripts/validate_reference_case_package.py --package-dir data/demo_cases/meta_q3_2022/demo/multimodal --prefix meta
git diff --check
```

## Tests Run And Results

- `PYTHONPATH=src pytest -q tests/test_reference_case_standard.py tests/test_meta_multimodal_panel.py tests/test_nlp_sidecars_evaluate.py`
  - result: `19 passed`
- `PYTHONPATH=src python3 scripts/build_meta_multimodal_panel.py --device auto --visual-sample-fps 0 --models finbert_tone financial_roberta`
  - result: bundle regenerated cleanly
- `PYTHONPATH=src python3 scripts/validate_reference_case_package.py --package-dir data/demo_cases/meta_q3_2022/demo/multimodal --prefix meta`
  - result: `valid: true`
- `git diff --check`
  - result: clean at verification time
