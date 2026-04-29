# Privacy Redaction

## Implemented Now

- deterministic fallback PII redaction in `src/signal_engine/privacy.py`
- hashing-only redaction records with no raw PII in reports
- support for email, phone, credit card-like, IBAN-like, and simple address patterns
- structure-preserving conversation redaction

## How To Run

The text emotion benchmark can redact before classification:

```bash
python scripts/run_text_emotion_benchmark.py \
  --input data/signal_engine_2_0/emotion_benchmark/sample_emotion_cases.jsonl \
  --manifest data/signal_engine_2_0/dataset_manifests/emotion_benchmark_manifest.json \
  --mode deterministic \
  --redact-pii \
  --out-dir outputs/signal_engine_2_0/text_emotion_benchmark
```

## Limitations

- this is a deterministic fallback, not a full NER or compliance suite
- name redaction is intentionally conservative to avoid over-redaction
- regex-based detection can miss edge cases or unusual formats
- redaction improves safety for fixtures and local benchmarking, not final governance

## Roadmap

- optional Presidio enhancement through `signal_engine.adapters.privacy`
- expanded policy controls once approved enterprise datasets exist
- deeper review workflows for audio/video-derived transcripts later
