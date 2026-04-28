# Signal Engine 2.0

Signal Engine 2.0 is a transcript-first, deterministic conversation intelligence scaffold for evidence-backed review of earnings calls, support conversations, sales calls, and account-management conversations.

The current branch prioritizes reproducible local analysis and evaluation readiness. It does not claim validated ML, statistical significance, market prediction, production retrieval, or production multimodal intelligence.

## What Works Now

- Deterministic support, sales, and account-management transcript analysis through `scripts/signal_engine_analyze.py`.
- Legacy support-QA MVP paths remain available through `src/parser.py`, `src/features.py`, and `src/pipeline.py`.
- Corpus manifest validation, gold-label validation, model registry validation, and training/evaluation-set registry validation.
- Deterministic weak-label keyword baseline for local `.txt` excerpts.
- Manual corpus case scaffolding from manifest rows.
- Metadata-only SEC 8-K intake helper that requires a user agent and does not fetch transcripts or exhibits.
- Buyer/demo artifacts under `demo/signal_engine_2_0/`.

## Scaffolded Only

- Model and dataset registries are planning/audit surfaces, not proof of implementation or validation.
- Weak-label outputs are deterministic review aids, not manual gold labels or validated training data.
- Handcrafted fixtures are smoke-test examples, not real validated training data.
- Optional sklearn training is local-only smoke scaffolding and writes no model artifact unless explicitly requested.
- SEC metadata intake saves only small metadata files when invoked; it does not create a corpus.

## Not Proven

- No full real earnings-call corpus is committed.
- No model weights are committed.
- No production ML exists on this branch.
- No statistical significance or market-reaction correlation is claimed.
- No validated embedding retrieval, reranker benchmark, or long-context benchmark exists yet.
- The first credible milestone remains 30 manually reviewed real earnings calls, followed later by a 100-150 call benchmark.

## Quick Start

Run the current deterministic conversation demos:

```bash
python scripts/signal_engine_analyze.py --domain support data/signal_engine_2_0/sample_support.json
python scripts/signal_engine_analyze.py --domain sales data/signal_engine_2_0/sample_sales.json
python scripts/signal_engine_analyze.py --domain account_management data/signal_engine_2_0/sample_account_management.json
```

Run the buyer demo pack:

```bash
python scripts/run_signal_engine_2_0_demo.py
```

Run the legacy support-QA MVP:

```bash
python scripts/analyze_conversation.py data/sample_conversations.json
```

## Lightweight Validation

Compile the current script surface:

```bash
python -m py_compile scripts/*.py
```

Run the focused evaluation-readiness tests:

```bash
python -m pytest tests/test_validate_corpus_manifest.py tests/test_validate_gold_labels.py tests/test_evaluate_signal_outputs.py tests/test_validate_model_registry.py tests/test_validate_training_sets_registry.py tests/test_run_weak_label_baseline.py tests/test_train_text_classifier_baseline_smoke.py -q
```

Check README and docs links:

```bash
python scripts/check_markdown_links.py README.md docs/*.md
```

## Corpus And Label Validation

Validate example corpus manifests:

```bash
python scripts/validate_corpus_manifest.py --path data/corpus_manifest.example.csv
python scripts/validate_corpus_manifest.py --path data/corpus_manifest.example.json
```

Validate example gold-label rows:

```bash
python scripts/validate_gold_labels.py --path data/gold_labels.example.jsonl
```

These examples are schema and evaluator fixtures only. They are not a validated training set.

## Model And Dataset Registry Validation

Validate the model registry:

```bash
python scripts/validate_model_registry.py --path data/model_registry.example.json
```

Validate the training/evaluation-set registry:

```bash
python scripts/validate_training_sets_registry.py --path data/training_sets_registry.example.csv
python scripts/validate_training_sets_registry.py --path data/training_sets_registry.example.json
```

Tracked model and dataset candidates are not automatically implemented, downloaded, licensed, or validated.

## Weak-Label Baseline

Run the deterministic weak-label baseline on a local transcript text file:

```bash
python scripts/run_weak_label_baseline.py --input tests/fixtures/tiny_realistic_earnings_excerpt.txt --case-id TEST_2026_Q1 --out /tmp/tiny_predictions.jsonl
```

Compare predictions against a gold-label JSONL file:

```bash
python scripts/evaluate_signal_outputs.py --gold-labels data/gold_labels.example.jsonl --predictions /tmp/tiny_predictions.jsonl --report-out /tmp/tiny_eval.md --json-out /tmp/tiny_eval.json
```

The weak-label baseline is deterministic keyword/rule logic, not trained ML.

## Manual 30-Call Corpus Intake

Start from the manual target list and example manifest:

```bash
python scripts/build_manual_corpus_case.py --manifest data/corpus_manifest.example.csv --case-id NVDA_2026_Q4 --out-root /tmp/manual_cases
```

Manual intake still requires source confirmation, licensing checks, local transcript handling, section review, speaker-role review, manual labels, and evidence-span review. Do not commit raw transcripts unless explicitly approved.

## SEC Metadata Intake

Fetch small SEC 8-K metadata only when you have a valid SEC user agent:

```bash
python scripts/fetch_sec_8k_index.py --ticker NVDA --user-agent "Your Name your.email@example.com" --limit 5 --json-out /tmp/nvda_8k.json
```

This helper does not fetch transcript text, exhibits, PDFs, audio, video, or paid/API outputs.

## NLP Research Map

The repo now tracks NLP tools, research references, model candidates, and training/evaluation set candidates so future work can be evaluated deliberately.

- [NLP tools and research map](docs/nlp-tools-and-research-map.md)
- [Training set plan](docs/training-set-plan.md)
- [Model registry](docs/model-registry.md)
- [Benchmark matrix plan](docs/benchmark-matrix-plan.md)

These registries are tracking surfaces only. Nothing is downloaded by adding a registry row, no datasets or models are shipped, no ML is validated, and deterministic transcript-first extraction remains the core system.

## Key Docs

- [Corpus build plan](docs/corpus-build-plan.md)
- [Ideal 30-call download list](docs/ideal-30-call-download-list.md)
- [Corpus evaluation implementation report](docs/corpus-evaluation-implementation-report.md)
- [NLP tools and research map](docs/nlp-tools-and-research-map.md)
- [Model registry](docs/model-registry.md)
- [Training set plan](docs/training-set-plan.md)
- [Benchmark matrix plan](docs/benchmark-matrix-plan.md)
- [Manual transcript download guide](docs/manual-transcript-download-guide.md)
- [SEC EDGAR intake guide](docs/sec-edgar-intake-guide.md)
- [Signal Engine 2.0 product notes](docs/signal-engine-2.0.md)
- [Domain schemas](docs/domain-schemas.md)
- [Multimodal stack notes](docs/multimodal-stack.md)
- [Library evaluation matrix](docs/library-evaluation-matrix.md)

## Architecture Boundary

Transcript-first deterministic extraction remains canonical. Optional audio, video, retrieval, embeddings, rerankers, long-context review, and sklearn experiments are roadmap or scaffolded evaluation surfaces only unless separately validated against a manually reviewed corpus.
