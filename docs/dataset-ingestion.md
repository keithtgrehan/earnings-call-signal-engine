# Dataset Ingestion

## Implemented Now

- JSONL fixture loading in `src/signal_engine/dataset_ingestion.py`
- fixture-level validation for text emotion benchmark rows
- manifest validation for local handcrafted datasets
- dataset card summaries for reporting

## How To Run

The benchmark runner validates the manifest and fixture before execution:

```bash
python scripts/run_text_emotion_benchmark.py \
  --input data/signal_engine_2_0/emotion_benchmark/sample_emotion_cases.jsonl \
  --manifest data/signal_engine_2_0/dataset_manifests/emotion_benchmark_manifest.json \
  --mode deterministic \
  --out-dir outputs/signal_engine_2_0/text_emotion_benchmark
```

## Limitations

- current validation is scoped to local handcrafted fixtures
- no dataset downloads or large-corpus orchestration are included
- no token-gated, licensed, or remote sources are fetched automatically

## Roadmap

- approved local dataset roots for richer benchmark slices
- stricter multimodal manifest validation when audio/video fixtures are added
- benchmark ingestion for licensed datasets only after user-provided paths, approvals, and privacy controls
