# Netflix Q1 2022 Multimodal Review Bundle

This folder is a persistent, reviewed support pack for the fixed Netflix demo case.

Boundary:
- deterministic transcript-backed artifacts remain canonical
- NLP sidecars, audio cues, and visual cues are supporting only
- nothing here implies predictive edge or statistical significance

Start with:
- `netflix_multimodal_panel.md`
- `netflix_multimodal_panel.json`
- `netflix_model_comparison.json`
- `netflix_disagreement_hotspots.json`

Supporting files:
- `netflix_multimodal_moment_manifest.json`: the bounded 11-moment curated set and top-8 showcase subset
- `netflix_pressure_moments_panel.json`: Q&A-only pressure review rows
- `netflix_disagreement_hotspots_panel.json`: prioritized sidecar disagreement review rows
- `netflix_audio_support.json`: curated audio support aligned to the existing timed Q&A windows
- `netflix_visual_support.json`: bounded visual support for the same timed windows when quality was usable
- `netflix_clip_manifest.json`: clip-ready ranges for later UI or reviewer playback work
- `netflix_supporting_only_caveats.json`: reviewer caveats that should travel with any later UI surfacing

The main generation path is:

```bash
PYTHONPATH=src python3 scripts/build_netflix_multimodal_panel.py \
  --device auto \
  --visual-sample-fps 0.25
```
