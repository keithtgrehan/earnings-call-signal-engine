# Netflix Multimodal Panel Summary

## What Ran

- Curated moment manifest generated for `netflix_q1_2022` with `11` bounded moments and a top-8 showcase subset.
- Sidecar models requested: `finbert_tone, financial_roberta, deberta_zero_shot, mpnet_embeddings`
- Visual sample FPS: `0.25`
- Requested exact MP4 path: `/Users/keith/Desktop/Netflix Meta Nvidia Capstone FINAL SOURCE/Netflix Q1 2022 Earnings Interview.mp4`
- Requested exact MP4 path matched directly: `False`
- Resolved local MP4 fallback used: `/Users/keith/Desktop/Netflix Meta Nvidia Capstone FINAL SOURCE/Netflix/Netflix Q1 2022 Earnings Interview.mp4`
- Sidecar execution mode: reused existing curated intermediate outputs for all requested models (`skipped_resume`).

## Exact Commands

- `PYTHONPATH=src python3 scripts/build_netflix_multimodal_panel.py --device auto --visual-sample-fps 0.25`

## Pairwise Sidecar Comparison

- Visual support mode: `heuristic_fallback` (observational fallback only; no model-backed visual scoring)
- `deberta_zero_shot` vs `financial_roberta`: comparable-label agreement `0.4545` across `11` curated moments.
- `deberta_zero_shot` vs `finbert_tone`: comparable-label agreement `0.2727` across `11` curated moments.
- `financial_roberta` vs `finbert_tone`: comparable-label agreement `0.6364` across `11` curated moments.

## What Was Skipped

- Visual skipped: `False`
- Uploaded transcript fallback present: `False`
- Uploaded shareholder-letter fallback present: `False`

## Outputs To Inspect First

- `/Users/keith/Documents/New project/main-demo-wt/data/demo_cases/netflix_q1_2022/demo/multimodal/netflix_multimodal_panel.json`
- `/Users/keith/Documents/New project/main-demo-wt/data/demo_cases/netflix_q1_2022/demo/multimodal/netflix_multimodal_panel.md`
- `/Users/keith/Documents/New project/main-demo-wt/data/demo_cases/netflix_q1_2022/demo/multimodal/netflix_model_comparison.json`
- `/Users/keith/Documents/New project/main-demo-wt/data/demo_cases/netflix_q1_2022/demo/multimodal/netflix_disagreement_hotspots.json`

## Known Limitations

- Audio remains limited to the curated Q&A windows already aligned in the repo.
- The exact requested local MP4 path did not match; this bundle used a fallback local Netflix MP4 for the bounded visual pass.
- The provided `/mnt/data` fallback PDFs were not present in this environment, so the repo-local transcript and shareholder-letter sources were used.
- Visual coverage is bounded to those timed Q&A windows and should be suppressed if the quality gate is weak.
- Visual support is currently heuristic fallback only and does not include model-backed visual scoring.
- Sidecars are supporting-only and do not replace the deterministic Netflix demo artifacts.

## Recommended Next Step

- Review the top-8 showcase moments first, then scan the disagreement hotspots before considering any UI surfacing.
