# Reference Case Parity Check

## What Was Checked

- Netflix branch:
  - `data/demo_cases/netflix_q1_2022/demo/multimodal/netflix_multimodal_panel.json`
  - `data/demo_cases/netflix_q1_2022/demo/multimodal/netflix_multimodal_panel.md`
  - `data/demo_cases/netflix_q1_2022/demo/multimodal/netflix_model_comparison.json`
  - `data/demo_cases/netflix_q1_2022/demo/multimodal/netflix_disagreement_hotspots.json`
  - `data/demo_cases/netflix_q1_2022/demo/multimodal/netflix_pressure_moments_panel.json`
  - `docs/netflix_reference_case_handoff.md`
- Meta branch:
  - `data/demo_cases/meta_q3_2022/demo/multimodal/meta_multimodal_panel.json`
  - `data/demo_cases/meta_q3_2022/demo/multimodal/meta_multimodal_panel.md`
  - `data/demo_cases/meta_q3_2022/demo/multimodal/meta_model_comparison.json`
  - `data/demo_cases/meta_q3_2022/demo/multimodal/meta_disagreement_hotspots.json`
  - `data/demo_cases/meta_q3_2022/demo/multimodal/meta_pressure_moments_panel.json`
  - `docs/meta_multimodal_handoff_summary.md`

## Issues Found

- The top-level panel contracts are now close, but one small structural parity gap remained: Netflix pressure-panel rows already carried `why_selected` while Meta pressure-panel rows did not.
- The remaining differences after that check were intentional case-shape differences rather than reviewer-safety defects.

## What Was Corrected

- On `feat/meta-q3-2022-reference-case`, added `why_selected` to persisted Meta pressure-panel rows so the Netflix and Meta pressure payloads now expose the same reviewer-context field.
- Re-ran the focused Meta panel regression after the parity change.

## What Remains Acceptable But Worth Reviewer Attention

- Netflix still uses the legacy grouped caveat payload shape while Meta uses the flat id-list caveat payload. The shared validator accepts both.
- Netflix persists a bounded heuristic-fallback visual artifact with `status: ok`; Meta persists an explicit case-level visual skip artifact with `status: skipped`. This is intentional.
- Netflix still exposes `cleaner_sidecar_examples` while Meta exposes `strong_supporting_context_moments`. The semantics are similar, but the field names are still not identical.
- Meta panel rows include `timestamp_range` for timed rows; Netflix panel rows do not currently expose that extra field.
- Netflix still uses `docs/netflix_reference_case_handoff.md` while Meta uses `docs/meta_multimodal_handoff_summary.md`. The content structure is aligned enough for review.

## Exact Commands Run

```bash
jq 'keys' "/Users/keith/Documents/New project/main-demo-wt/data/demo_cases/netflix_q1_2022/demo/multimodal/netflix_multimodal_panel.json"
jq 'keys' "/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-meta-reference-case/data/demo_cases/meta_q3_2022/demo/multimodal/meta_multimodal_panel.json"
jq '[.panel_rows[0] | keys[]]' "/Users/keith/Documents/New project/main-demo-wt/data/demo_cases/netflix_q1_2022/demo/multimodal/netflix_multimodal_panel.json"
jq '[.panel_rows[0] | keys[]]' "/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-meta-reference-case/data/demo_cases/meta_q3_2022/demo/multimodal/meta_multimodal_panel.json"
jq '[.rows[0] | keys[]]' "/Users/keith/Documents/New project/main-demo-wt/data/demo_cases/netflix_q1_2022/demo/multimodal/netflix_pressure_moments_panel.json"
jq '[.rows[0] | keys[]]' "/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-meta-reference-case/data/demo_cases/meta_q3_2022/demo/multimodal/meta_pressure_moments_panel.json"
PYTHONPATH=src pytest -q tests/test_meta_multimodal_panel.py
git diff --check
```

## Tests Run And Results

- `PYTHONPATH=src pytest -q tests/test_meta_multimodal_panel.py`
  - result: `12 passed`
- `git diff --check`
  - result: clean after the parity edit

## Branch Status

- parity audit doc updated on `chore/reference-case-standardization`
- parity fix landed on `feat/meta-q3-2022-reference-case`
- Netflix branch required no additional structural correction in this pass
