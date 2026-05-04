# Codex Project Context

## Canonical Project Goal

Build a multimodal communication intelligence engine for evidence-backed signal, sentiment, emotion proxy, and intent detection across business conversations.

The engine must support earnings/finance, B2B sales, account management/customer success, customer support, and HR/internal communication. Text remains the anchor. Audio and video are segment-level augmentation layers.

## Current Reality

- A working multimodal v1 scaffold exists.
- The local fixture run has `38` normalized records and `38` aligned segments.
- A text baseline artifact exists.
- Large/gated datasets are connector-tracked and skipped unless local files exist.
- No local audio/video-backed training benchmark exists yet.
- Audio/video outputs are limitation-aware in the current fixture run.
- Current self-consistency metrics are not a meaningful model-performance claim.
- Human gold labels remain the benchmark source.

## Non-Goals

- Do not claim SOTA.
- Do not claim production readiness.
- Do not claim emotion certainty.
- Do not claim alpha, trading edge, live trading value, stock prediction, or investment advice.
- Do not treat weak labels, model predictions, or LLM triage as gold labels.
- Do not spend remote compute before data/eval gates are met.

## Next Best Action Order

1. Build a real human-reviewed text benchmark from current call packets and review queues.
2. Save train/dev/test splits and benchmark manifests.
3. Train and compare text baselines on real held-out labels.
4. Add local aligned audio examples.
5. Evaluate audio-only and text+audio uplift.
6. Add local aligned video examples.
7. Evaluate video-only and text+audio+video uplift.
8. Scale active learning to rare, uncertain, and disagreement cases.
9. Prepare remote GPU configs only after benchmark and scripts are stable.

## Warnings For Future Runs

- Do not call the baseline meaningful until a real benchmark exists.
- Do not present self-consistency metrics as accuracy.
- Do not hide disagreement flags or uncertainty.
- Do not silently drop unavailable datasets, invalid rows, or missing media.
- Do not spend remote compute on scaffolding.
- Do not fine-tune transformers until gold labels, splits, configs, and MLflow tracking are ready.

## Preferred Development Style

- Keep changes additive and reproducible.
- Preserve provenance on every record.
- Keep human review minimal and targeted.
- Add tests for schema, stage contracts, metrics, and artifact generation.
- Prefer measurable evaluation over bigger model claims.
