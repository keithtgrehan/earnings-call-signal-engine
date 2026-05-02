# Remote Training Readiness

Remote compute is prepared but not justified yet.

## Current Gate

- Gold benchmark: not sufficient.
- Saved train/dev/test splits: not available.
- Transformer fine-tuning trigger: not met.
- Batch audio/video trigger: not met.

## Do Not Run Conditions

- Gold labels are below the training threshold.
- Only weak labels are available.
- No saved splits exist.
- No MLflow tracking destination is configured.
- Audio/video media is unaligned or unavailable.

## Required Before Remote GPU

1. Build `data/gold/gold_labels.jsonl` from accepted human reviews.
2. Reach at least `500` gold labels for full train/dev/test split readiness.
3. Save split manifests and checksums.
4. Run local baseline evaluation.
5. Package the run with `python tools/package_training_run.py`.

## Current Recommendation

Stay local. Spend no remote compute until the benchmark gate is met.
