# Meta Multimodal Panel Summary

## What Ran

- Curated moment manifest generated for `meta_q3_2022` with `12` bounded moments and a top-8 showcase subset.
- Sidecar models requested: `finbert_tone, financial_roberta`
- Visual sample FPS: `0.0`
- Requested exact MP4 path: `/Users/keith/Desktop/Netflix Meta Nvidia Capstone FINAL SOURCE/Meta/Facebook (META) Q3 2022 Earnings Call.mp4`
- Requested exact MP4 path matched directly: `True`
- Resolved local MP4 fallback used: `not needed`

## Exact Commands

- `PYTHONPATH=src python3 scripts/build_meta_multimodal_panel.py --device auto --visual-sample-fps 0 --models finbert_tone financial_roberta`

## How To Read This Pack

- Start with the transcript-backed deterministic rows and use this bundle as reviewer support only.
- A same-direction sidecar read is bounded same-direction context, not proof of correctness.
- A disagreement hotspot is a review priority, not a winner or loser among models.
- Audio stays on measured pause, filler, and qualification cues; visual stays observational only.

## Supporting-Layer Comparison Snapshot

- `financial_roberta` vs `finbert_tone`: comparable-label same-label rate `0.5` across `12` curated moments.

## What Was Skipped

- Visual support was skipped in the final persisted bundle: A bounded visual pass was intentionally skipped after earlier full-video heuristic attempts exceeded the reviewer-safe runtime cap in this session.

## Outputs To Inspect First

- `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-meta-reference-case/docs/meta_multimodal_asset_audit.md`
- `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-meta-reference-case/data/demo_cases/meta_q3_2022/demo/multimodal/meta_multimodal_panel.json`
- `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-meta-reference-case/data/demo_cases/meta_q3_2022/demo/multimodal/meta_multimodal_panel.md`
- `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-meta-reference-case/data/demo_cases/meta_q3_2022/demo/multimodal/meta_model_comparison.json`
- `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-meta-reference-case/data/demo_cases/meta_q3_2022/demo/multimodal/meta_disagreement_hotspots.json`
- `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-meta-reference-case/data/demo_cases/meta_q3_2022/demo/multimodal/meta_supporting_only_caveats.json`

## Known Limitations

- Audio remains limited to the two aligned main-call Q&A windows already present in the repo.
- Follow-up, presentation, and release moments do not have main-call video timestamps.
- Sidecars are supporting-only and do not replace the deterministic Meta Q3 2022 artifacts.

## Recommended Next Step

- Read the asset audit first, then review the top-8 showcase moments, then scan the ranked disagreement hotspots before any UI follow-up.
