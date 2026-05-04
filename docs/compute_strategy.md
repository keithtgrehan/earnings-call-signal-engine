# Compute Strategy

## Local Stage

Run locally while the project is still proving schemas, data contracts, review workflows, and evaluation logic.

Run locally:

- `python tools/run_full_pipeline.py --dry-run`
- `python tools/run_full_pipeline.py --stage all`
- Unit tests and lint checks.
- Dataset manifest validation.
- Small TF-IDF and sklearn baselines.
- Small fixture and seed-label experiments.
- Review-batch generation.

Do not use paid compute for local-stage tasks that only prove plumbing.

## Colab / RunPod / Paperspace Stage

Use short-lived GPU environments when real benchmark data and training configs are ready.

Good fits:

- Transformer fine-tuning on a real text benchmark.
- Batch audio feature extraction or embeddings for aligned media.
- Batch video feature extraction for a bounded media set.
- Larger ablation runs that are too slow locally but still exploratory.

Requirements before using this stage:

- Dataset manifests exist.
- Train/dev/test splits are saved.
- MLflow tracking is configured.
- Scripts can resume or restart safely.
- Expected artifact paths are known.

## Lambda Labs / AWS / GCP Later Stage

Use larger remote infrastructure only after the training loop is stable and scale justifies it.

Good fits:

- Repeatable large transformer training.
- `100+` calls with aligned media.
- Batch multimodal embeddings.
- Cross-domain model comparison.
- Longer-running experiments that need stable storage and scheduled jobs.

## What Not To Run Remotely Yet

- Unreviewed weak-label experiments with no gold benchmark.
- Unaligned audio/video media.
- One-off scaffolding scripts.
- Pipelines without saved config, split, and artifact expectations.
- Experiments that cannot be reproduced from a local smoke subset.

## Budget-Safe Rules

- Stay local until pipeline/schema/eval are stable.
- Pay for GPU only when a real benchmark and training config exist.
- Stop a remote run if it cannot write MLflow metrics and artifacts.
- Prefer smaller smoke jobs before full jobs.
- Record expected cost, data size, model, and success criteria before launching.

Remote compute trigger:

- `10k+` text examples.
- Transformer fine-tuning.
- Batch audio/video embeddings.
- `100+` calls with media.

## Artifact Sync Strategy

- Keep source data manifests in the repo.
- Keep large raw media outside git and reference it by manifest path/checksum.
- Sync trained models, metrics, predictions, and split manifests back to `models/`, `outputs/`, or `data/processed/` as appropriate.
- Do not overwrite gold labels with weak/model labels.
- Preserve provenance for every imported or generated row.

## MLflow Expectations

Every training or evaluation run should log:

- Experiment name and run ID.
- Git commit when available.
- Dataset manifest path and checksum.
- Train/dev/test split IDs.
- Model family and config.
- Metrics, confusion matrix, calibration, false positives, false negatives.
- Artifacts needed to reproduce or audit the run.
