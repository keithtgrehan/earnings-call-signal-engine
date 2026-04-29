# Text Emotion Benchmark

## Implemented Now

- a tiny handcrafted text emotion fixture in `data/signal_engine_2_0/emotion_benchmark/sample_emotion_cases.jsonl`
- a deterministic keyword baseline in `src/signal_engine/text_emotion_baseline.py`
- a runnable benchmark CLI in `scripts/run_text_emotion_benchmark.py`
- metrics and markdown reporting built on the pure-Python benchmark helpers

## How To Run

```bash
python scripts/run_text_emotion_benchmark.py \
  --input data/signal_engine_2_0/emotion_benchmark/sample_emotion_cases.jsonl \
  --manifest data/signal_engine_2_0/dataset_manifests/emotion_benchmark_manifest.json \
  --mode deterministic \
  --redact-pii \
  --out-dir outputs/signal_engine_2_0/text_emotion_benchmark
```

Optional local transformer mode:

```bash
python scripts/run_text_emotion_benchmark.py \
  --input data/signal_engine_2_0/emotion_benchmark/sample_emotion_cases.jsonl \
  --manifest data/signal_engine_2_0/dataset_manifests/emotion_benchmark_manifest.json \
  --mode transformers \
  --model-id j-hartmann/emotion-english-distilroberta-base \
  --out-dir outputs/signal_engine_2_0/text_emotion_benchmark_transformers
```

## Limitations

- the fixture is tiny and handcrafted
- deterministic keyword matching is only a harness baseline
- transformer mode requires optional dependencies and locally available model artifacts
- this is not production proof, psychological diagnosis, or truth detection

## Roadmap

- larger approved benchmark fixtures
- richer label mappings and calibration analysis
- optional local transformer comparisons
- later audio/video fusion only after transcript and privacy layers stay stable
