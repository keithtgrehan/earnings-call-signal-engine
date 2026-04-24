# Signal Engine 2.0 Review Package

## Executive Summary

Signal Engine 2.0 is a transcript-first, deterministic signal extraction layer for messy business conversations. Earnings calls are the primary portfolio and capstone use case, while support, sales, and account-management examples show that the same evidence-backed architecture generalizes to other business review workflows. Canonical output remains inspectable and reproducible. Emotion models, audio tooling, video tooling, and multimodal layers are optional benchmark or roadmap components only.

## What Works Now

- deterministic transcript analysis for support, sales, and account-management conversations
- unified JSON output with scores, flags, evidence, and metadata
- optional deterministic PII redaction before analysis
- deterministic text emotion benchmark harness with tiny handcrafted fixtures
- metadata registries, dataset ingestion, and import-safe optional adapters
- final demo orchestration via `python scripts/run_signal_engine_2_0_demo.py`

## How To Run

Core CLI:

```bash
python scripts/signal_engine_analyze.py --domain support data/signal_engine_2_0/sample_support.json
python scripts/signal_engine_analyze.py --domain sales data/signal_engine_2_0/sample_sales.json
python scripts/signal_engine_analyze.py --domain account_management data/signal_engine_2_0/sample_account_management.json
python scripts/signal_engine_analyze.py --domain support --redact-pii data/signal_engine_2_0/fixtures/support_tickets_realistic.jsonl
```

Benchmark:

```bash
python scripts/run_text_emotion_benchmark.py \
  --input data/signal_engine_2_0/emotion_benchmark/sample_emotion_cases.jsonl \
  --manifest data/signal_engine_2_0/dataset_manifests/emotion_benchmark_manifest.json \
  --mode deterministic \
  --redact-pii \
  --out-dir outputs/signal_engine_2_0/text_emotion_benchmark
```

Final demo:

```bash
python scripts/run_signal_engine_2_0_demo.py
```

## Output Artifacts

- final demo bundle under `outputs/signal_engine_2_0/final_demo/`
- deterministic benchmark outputs under `outputs/signal_engine_2_0/text_emotion_benchmark/`
- buyer-facing demo examples under `demo/signal_engine_2_0/`

## Validation Status

- deterministic CLI paths are covered by focused tests
- privacy redaction, dataset ingestion, benchmark runner, and demo script are covered by focused tests
- optional transformer benchmark was not run because dependency/model cache availability could not be confirmed quickly without risking a slow demo pass

## Legacy Portfolio CI Status

- `make portfolio-ci` no longer crashes when the local legacy `outputs/LLY_2025_Q2_call08/` artifact bundle is incomplete
- legacy proof refresh, freshness, and doc-audit steps now warn and skip cleanly when required local files such as `metrics.json` are missing
- the current Signal Engine 2.0 demo path stays deterministic and separate from that legacy proof bundle

## Business Value

- messy conversations and transcripts are hard to review consistently
- generic AI summaries are broad and difficult to audit
- converts raw transcripts into auditable support, sales, and account-management signals
- preserves evidence snippets for reviewer trust and downstream workflow design
- supports privacy-aware benchmarking without requiring external APIs

## Monetisation / Hire / Acquisition Relevance

- useful as a recruiter or hiring artifact because it demonstrates deterministic NLP, product boundary discipline, privacy safeguards, and extensibility
- useful as a buyer demo because outputs stay inspectable rather than opaque
- useful as acquisition diligence material because it shows a transcript-first core with optional growth paths rather than a fragile model-only prototype

## Roadmap

- optional transformer text emotion comparisons
- optional ASR and diarization when raw audio is available
- optional audio feature extraction and escalation-only video review
- optional retrieval and later multimodal fusion

## Intentionally Not Done

- no truth-detection claim
- no black-box emotion score as canonical truth
- no alpha claim or unsupported statistical significance claim
- no production ASR, production diarization, or production multimodal fusion
- no heavy required dependencies in the default path
