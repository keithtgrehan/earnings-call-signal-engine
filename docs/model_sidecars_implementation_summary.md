# Model Sidecars Implementation Summary

## What Was Added

- New optional `model_sidecars` package under `src/earnings_call_sentiment/model_sidecars/`
- Five model adapters:
  - `finbert_tone`
  - `financial_roberta`
  - `deberta_zero_shot`
  - `distilbart_zero_shot_smoke`
  - `mpnet_embeddings`
- Case/artifact loaders that reuse existing processed-case outputs for:
  - `chunks`
  - `guidance_spans`
  - `qa_answers`
  - `speaker_turns`
- Separate sidecar artifact writing under `outputs/<case_id>/model_sidecars/`
- New CLI paths:
  - `python3 -m earnings_call_sentiment sidecars ...`
  - `python3 -m earnings_call_sentiment sidecars-prewarm ...`
  - `python3 -m earnings_call_sentiment sidecars-benchmark ...`
  - `python3 -m earnings_call_sentiment sidecars-evaluate ...`
- New zero-shot label presets:
  - `configs/model_eval/zero_shot_labels.default.yaml`
  - `configs/model_eval/zero_shot_labels.finance.yaml`
- New evaluation script:
  - `scripts/evaluate_model_sidecars.py`
- New benchmark script:
  - `scripts/benchmark_model_sidecars.py`
- New manifest templates:
  - `configs/model_eval/manifests/*.template.yaml`
- New docs:
  - `docs/model_sidecars.md`
- Focused sidecar tests plus runtime-hardening follow-up work

## Commands To Run

### Sidecars

```bash
PYTHONPATH=src python3 -m earnings_call_sentiment sidecars \
  --case-id nvidia_q4_fy2024 \
  --models finbert_tone financial_roberta deberta_zero_shot mpnet_embeddings \
  --units chunks guidance_spans qa_answers \
  --zero-shot-label-config configs/model_eval/zero_shot_labels.finance.yaml \
  --output-dir outputs
```

### Evaluation

```bash
PYTHONPATH=src python3 scripts/evaluate_model_sidecars.py \
  --case-id nvidia_q4_fy2024 \
  --sidecar-root outputs
```

## Known Limitations

- First-time model downloads and initialization for `deberta_zero_shot` and `mpnet_embeddings` can be materially slower on CPU than the two finance classifiers.
- The slower zero-shot and embedding runs are best validated with reduced CPU samples before broader benchmark runs.
- `speaker_turns` only runs when clean speaker-turn artifacts already exist.
- Prior-quarter guidance similarity uses existing `guidance_revision.csv` pairs when available; otherwise MPNet falls back to within-case nearest-neighbor similarity.
- Sidecars remain optional supporting layers only. Deterministic transcript-first outputs remain canonical.

## Scope Notes

- The current sidecar branch spans code, docs, manifests, dependency metadata, benchmark helpers, and focused tests.
- It is narrower than the multimodal or demo-surface branches and should be reviewed as optional runtime/comparison support only.
- Use the sidecar commit history and `git show --stat` if you need the original feature-only footprint rather than a hand-picked file summary.
