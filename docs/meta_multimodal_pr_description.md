# Meta Q3 2022 Multimodal Reference Case

## Summary

This branch adds one bounded Meta Q3 2022 multimodal review pack built to the same reviewer-safe standard as the Netflix reference case, while keeping deterministic transcript-backed outputs canonical.

## What Changed

- added optional NLP sidecar infrastructure and CLI for bounded review packs
- ported the small reference-case package validator from the reference-standardization branch
- added a Meta-specific multimodal bundle builder with:
  - a 12-moment curated manifest
  - a top-8 showcase subset
  - model-comparison and disagreement outputs
  - bounded audio support reuse from the committed curated Q&A windows
  - an explicit visual skip artifact after bounded heuristic attempts exceeded the runtime cap
- wrote the persistent Meta reviewed bundle under `data/demo_cases/meta_q3_2022/demo/multimodal/`
- wrote the Meta asset audit, evidence-panel doc, panel summary, PR description, and handoff summary

## Guardrails Preserved

- deterministic transcript-first remains canonical
- sidecars, audio, and video remain supporting-only
- Meta Q3 2022 only
- bounded review pack for demo and later UI follow-up
- no predictive claims
- no statistical-significance claims
- `main` untouched

## Runtime Notes

- final persisted NLP sidecar bundle used `finbert_tone` and `financial_roberta`
- `deberta_zero_shot` and `mpnet_embeddings` were attempted in the first wider run but were not kept in the final persisted bundle after the bounded runtime cap was applied
- the exact requested local Meta MP4 path matched directly
- final persisted visual output was intentionally skipped after earlier full-video heuristic attempts exceeded the reviewer-safe runtime cap

## Reviewer Start Points

- `docs/meta_multimodal_asset_audit.md`
- `data/demo_cases/meta_q3_2022/demo/multimodal/meta_multimodal_panel.json`
- `data/demo_cases/meta_q3_2022/demo/multimodal/meta_multimodal_panel.md`
- `data/demo_cases/meta_q3_2022/demo/multimodal/meta_model_comparison.json`
- `data/demo_cases/meta_q3_2022/demo/multimodal/meta_disagreement_hotspots.json`

