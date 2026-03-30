# Meta Multimodal Handoff Summary

## What Was Run

- bounded Meta manifest generation for `meta_q3_2022`
- optional NLP sidecar comparison using `finbert_tone` and `financial_roberta`
- reuse of the committed curated audio support rows for two main-call Q&A moments
- reference-case package validation on the final persistent bundle
- focused branch-relevant test suite plus `git diff --check`

## Exact Commands

```bash
PYTHONPATH=src python3 scripts/run_nlp_sidecars.py compare --case-id meta_q3_2022
PYTHONPATH=src python3 scripts/build_meta_multimodal_panel.py --device auto --visual-sample-fps 0.25
PYTHONPATH=src python3 scripts/build_meta_multimodal_panel.py --device auto --visual-sample-fps 0.25 --models finbert_tone financial_roberta
PYTHONPATH=src python3 scripts/build_meta_multimodal_panel.py --device auto --visual-sample-fps 0.1 --models finbert_tone financial_roberta
PYTHONPATH=src python3 scripts/build_meta_multimodal_panel.py --device auto --visual-sample-fps 0 --models finbert_tone financial_roberta
PYTHONPATH=src python3 scripts/validate_reference_case_package.py --package-dir data/demo_cases/meta_q3_2022/demo/multimodal --prefix meta
PYTHONPATH=src pytest -q tests/test_audio_behavior.py tests/test_multimodal_support.py tests/test_visual_behavior.py tests/test_nlp_sidecars_config.py tests/test_nlp_sidecars_evaluate.py tests/test_nlp_sidecars_io.py tests/test_nlp_sidecars_runner.py tests/test_run_nlp_sidecars.py tests/test_reference_case_standard.py tests/test_meta_multimodal_panel.py
git diff --check
```

## Media Actually Available

- exact requested local MP4 path matched directly:
  - `/Users/keith/Desktop/Netflix Meta Nvidia Capstone FINAL SOURCE/Meta/Facebook (META) Q3 2022 Earnings Call.mp4`
- repo-local source files available:
  - main earnings call transcript PDF
  - follow-up call transcript PDF
  - Q3 2022 results release PDF
  - Q3 2022 earnings presentation PDF
- repo-local committed audio support available:
  - `processed/audio_behavior/audio_status.json`
  - `processed/audio_behavior/audio_behavior_summary.json`
  - two aligned main-call Q&A review rows in `processed/audio_behavior/audio_review_rows.json`

## What Was Skipped

- final persisted visual output:
  - skipped
  - reason: earlier full-video heuristic attempts at `0.25` FPS and `0.1` FPS exceeded the reviewer-safe runtime cap for this session
- final persisted zero-shot / embedding sidecars:
  - not included
  - reason: the wider first pass completed `finbert_tone` and `financial_roberta`, but the optional `deberta_zero_shot` and `mpnet_embeddings` leg was bounded out rather than allowed to block the final pack

## Outputs To Inspect First

- `docs/meta_multimodal_asset_audit.md`
- `docs/meta_multimodal_evidence_panel.md`
- `docs/meta_multimodal_panel_summary.md`
- `data/demo_cases/meta_q3_2022/demo/multimodal/meta_multimodal_panel.json`
- `data/demo_cases/meta_q3_2022/demo/multimodal/meta_model_comparison.json`
- `data/demo_cases/meta_q3_2022/demo/multimodal/meta_disagreement_hotspots.json`
- `data/demo_cases/meta_q3_2022/demo/multimodal/meta_audio_support.json`
- `data/demo_cases/meta_q3_2022/demo/multimodal/meta_visual_support_skipped.json`

## Known Limitations

- visual behavior is not persisted in the final bundle because the bounded full-video heuristic attempts were capped out
- only two main-call Q&A moments have curated audio timing support
- follow-up, release, and presentation moments do not have main-call video timestamps
- final sidecar comparison is limited to two classification models
- sidecar disagreement is a review priority, not validation or adjudication

## Why This Pack Is Bounded And Reviewer-Safe

- deterministic transcript-backed outputs stay canonical
- support layers are explicit optional context only
- weak or unavailable support stays explicit as `unavailable` or `skipped`
- the visual layer does not imply corroboration because the final bundle carries an explicit skip artifact
- no predictive-edge claims
- no statistical-significance claims

## Recommended Next Step After Review

- review the top-8 showcase moments and the ranked disagreement hotspots first
- if reviewers still want visual context, run a separate clip-only visual follow-up on the two aligned main-call Q&A windows instead of reopening a full-video heuristic pass
- if additional NLP breadth is still useful after review, run `deberta_zero_shot` and `mpnet_embeddings` as a separate bounded follow-up rather than reopening this reviewer pack
