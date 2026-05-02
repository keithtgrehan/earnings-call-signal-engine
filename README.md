# Multimodal Communication Intelligence Engine

This project is a transcript-first multimodal NLP engine for measurable communication signals across business conversations. It combines deterministic text signals, sentiment and emotion inference, audio behavioral features, video engagement features, multimodal fusion, ensemble voting, active learning, and conservative evaluation.

The current system is a working v1 scaffold and fixture baseline. It is not yet a serious trained multimodal model, not a production-ready system, and not evidence of state-of-the-art performance.

## Product Scope

Target domains:

- Earnings calls / finance.
- B2B sales.
- Account management / customer success.
- Customer support.
- HR / internal communication.

Core tasks:

- Text signal detection.
- Sentiment classification.
- Probabilistic emotion inference.
- Intent, commitment, uncertainty, risk, and friction detection.
- Audio behavioral feature extraction.
- Video behavioral and engagement feature extraction.
- Multimodal fusion.
- Ensemble decisioning with visible disagreement.
- Active-learning review selection.
- Cross-domain evaluation.

## Current State

The repo now contains a working multimodal v1 pipeline:

- `src/data_layer`
- `src/alignment`
- `src/text_engine`
- `src/audio_engine`
- `src/video_engine`
- `src/fusion`
- `src/ensemble`
- `src/training`
- `src/active_learning`
- `tools/run_full_pipeline.py`
- `tools/export_review_batch.py`
- `tools/import_review_labels.py`

The latest fixture-backed pipeline run produced:

- `38` normalized records.
- `38` aligned segments.
- `38` ensemble outputs.
- `25` active-learning review candidates plus CSV header.
- A text baseline artifact at `models/multimodal_engine/text_signal_baseline.joblib`.
- MLflow tracking artifacts under `data/processed/multimodal_engine/mlruns`.

Large or gated datasets are connector-tracked and explicitly marked skipped unless local files are available. Missing data is not silently dropped.

## What Works Now

- Manifest-driven ingestion for the requested dataset families.
- Canonical normalized record and segment contracts.
- Transcript-first alignment for fixture and local text data.
- Deterministic business signal labeling for `risk_friction`, `opportunity_commitment`, `uncertainty_hedging`, and `neutral`.
- Baseline sentiment and emotion proxy scoring.
- Audio and video stage outputs with explicit `available`, `limitations`, and adapter metadata.
- Text-anchored fusion.
- Ensemble outputs with visible votes, confidence, uncertainty, evidence, and disagreement flags.
- Active-learning review batch generation.
- Local text baseline training when the existing human-reviewed seed labels meet support gates.
- Reproducible local validation through `pytest` and `ruff`.

## What Is Not Proven Yet

- No validated multimodal benchmark exists yet.
- No real local audio/video-backed training set exists yet unless media is added.
- No cross-domain generalization claim is valid yet.
- No production ML performance claim is valid yet.
- No unsupported emotion certainty claims are made.
- No alpha, live trading, market reaction, stock prediction, or investment advice claims are made.
- Weak labels, model predictions, and optional LLM triage are not gold labels.

## How To Run Locally

Readiness check:

```bash
python tools/run_full_pipeline.py --dry-run
```

Run the bounded local pipeline:

```bash
python tools/run_full_pipeline.py --stage all
```

Run validation:

```bash
pytest -q
ruff check .
```

Primary outputs:

- `data/processed/multimodal_engine/normalized_records.jsonl`
- `data/processed/multimodal_engine/aligned_segments.jsonl`
- `data/processed/multimodal_engine/text_predictions.jsonl`
- `data/processed/multimodal_engine/audio_features.jsonl`
- `data/processed/multimodal_engine/video_features.jsonl`
- `data/processed/multimodal_engine/fusion_predictions.jsonl`
- `data/processed/multimodal_engine/ensemble_outputs.jsonl`
- `data/processed/multimodal_engine/next_review_batch.csv`
- `data/processed/multimodal_engine/evaluation_results.json`
- `data/processed/multimodal_engine/training_status.json`

## Current Baseline Meaning

The trained text baseline is a local fixture/seed-label baseline. It is useful for proving the training path, artifact writing, metrics plumbing, and MLflow integration.

It does not mean:

- The model is ready for production.
- The model generalizes across target domains.
- The reported smoke/self-consistency metrics are real-world accuracy.
- Multimodal uplift has been demonstrated.
- Emotion inference is certain or directly observed.

## Maturity Definitions

- Scaffold: Code paths, schemas, stages, artifacts, and validation exist.
- Trained baseline: A model is trained on a bounded local dataset with recorded splits and metrics.
- Validated model: A model is evaluated on a real held-out benchmark with human gold labels and known limitations.
- Production-ready system: A validated model plus monitoring, calibration, privacy controls, failure handling, reproducible deployments, and operational review processes.

The current project is between scaffold and fixture baseline. It is not yet a validated model.

## Next Milestones

1. Build a real labeled benchmark from current call packets and review queues.
2. Scale the text dataset with provenance-preserving ingestion and human gold review.
3. Add local audio/video examples with aligned timestamps.
4. Train a meaningful text baseline and compare TF-IDF, transformer, FinBERT, DeBERTa, and RoBERTa candidates.
5. Run cross-domain evaluation across earnings, support, sales, account management, and HR/internal communication.
6. Prepare remote GPU training only after benchmark, splits, configs, and MLflow tracking are stable.

## Key Docs

- [Project goals and scope](docs/project_goals_and_scope.md)
- [Roadmap to trained model](docs/roadmap_to_trained_model.md)
- [Compute strategy](docs/compute_strategy.md)
- [Codex project context](docs/codex_project_context.md)
- [Implementation handoff](docs/implementation_handoff.md)
- [System architecture](docs/system_architecture.md)
- [Evaluation results](docs/evaluation_results.md)
- [Model performance](docs/model_performance.md)
- [Multimodal analysis](docs/multimodal_analysis.md)
