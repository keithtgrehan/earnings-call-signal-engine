# Netflix Q1 2022 Multimodal Review Bundle

This folder is a persistent, reviewed support pack for the fixed Netflix demo case.

Boundary:
- deterministic transcript-backed artifacts remain canonical
- NLP sidecars, audio cues, and visual cues are supporting only
- nothing here implies predictive edge or statistical significance

Start with:
- `docs/netflix_multimodal_asset_audit.md`
- `docs/netflix_multimodal_panel_summary.md`
- `netflix_multimodal_panel.md`
- `netflix_multimodal_panel.json`
- `netflix_model_comparison.json`
- `netflix_disagreement_hotspots.json`
- `netflix_supporting_only_caveats.json`

Supporting files:
- `netflix_multimodal_moment_manifest.json`: the bounded 11-moment curated set and top-8 showcase subset
- `netflix_pressure_moments_panel.json`: Q&A-only pressure review rows
- `netflix_disagreement_hotspots_panel.json`: prioritized sidecar disagreement review rows
- `netflix_audio_support.json`: curated audio support aligned to the existing timed Q&A windows
- `netflix_visual_support.json`: bounded visual support for the same timed windows when quality was usable
- `netflix_clip_manifest.json`: clip-ready ranges plus rank/showcase metadata for later UI or reviewer playback work
- `netflix_supporting_only_caveats.json`: reviewer caveats that should travel with any later UI surfacing

The main generation path is:

```bash
PYTHONPATH=src python3 scripts/build_netflix_multimodal_panel.py \
  --device auto \
  --visual-sample-fps 0.25
```

For the committed review bundle, the exact requested local MP4 path did not match. A fallback local Netflix MP4 was found and used for the bounded supporting-only visual pass, and the resulting visual support stayed in heuristic fallback mode rather than model-backed scoring.

Recommended read order:
- confirm the requested-path vs fallback-path distinction in `docs/netflix_multimodal_asset_audit.md`
- scan `docs/netflix_multimodal_panel_summary.md` for current limitations and file order
- review `netflix_multimodal_panel.md` for the top-8 showcase and moment-level notes
- use `netflix_disagreement_hotspots.json` only after the canonical transcript-backed moments are understood
