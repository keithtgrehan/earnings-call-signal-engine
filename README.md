# Signal Engine

Signal Engine is a deterministic-first signal extraction and evaluation system for long-form business communication.

The strongest proof path is earnings-call transcripts because public-company sources, explicit guidance language, analyst Q&A, and evidence-span review create a credible route to repeatable evaluation. Broader domains are supported or scaffolded where the same transcript-first pattern applies: customer support, sales calls, account management, churn risk, and general dialogue tone/emotion benchmarks.

This repo does not claim production ML, statistical significance, market-reaction proof, production retrieval, or validated multimodal intelligence.

## What Works Now

- Deterministic transcript and signal scaffolds for evidence-backed review.
- Earnings-call corpus manifest validation.
- Gold-label JSONL validation.
- Model, dataset, and NLP tools registries.
- SEC 8-K metadata-only intake.
- Manual corpus case setup.
- Deterministic weak-label keyword baseline for local `.txt` transcripts.
- First 3 earnings-call intake cases: `NVDA_2026_Q4`, `META_2025_Q4`, and `AMZN_2025_Q4`.
- Repo validation and documentation checks.

## Scaffolded Only

- Sales, support, and account-management use cases beyond the deterministic demo/sample layer.
- Public dataset and model candidates.
- Embeddings, rerankers, and long-context model candidates.
- Optional local sklearn training scaffold.
- Emotion/tone dataset references.

Scaffolded means tracked, documented, or locally runnable as a smoke check. It does not mean validated, production-ready, or trained.

## Not Proven

- No real 30-call corpus yet.
- No validated ML.
- No statistical significance.
- No market-reaction proof.
- No production retrieval stack.
- No validated sales/support/account benchmark.
- No committed raw transcripts, datasets, model weights, audio, video, or API outputs.

## Why Earnings Calls Remain The Proof Path

- Public-company source availability makes provenance review possible.
- Signal types such as guidance revision, uncertainty, analyst pressure, and Q&A friction can be tied to explicit transcript evidence.
- Manual evidence-span review is practical before scaling.
- The repo has a clear path from the first 3 manually reviewed calls to a 30-call benchmark, then a 100-150-call benchmark.

## Broader Use-Case Map

- Earnings calls: guidance, uncertainty, analyst pressure, Q&A friction.
- Customer support: escalation, unresolved issue, directness, deflection, tone shift.
- Sales calls: objections, buying intent, pricing concern, next-step clarity.
- Account management: churn risk, renewal concern, expansion opportunity, stakeholder friction.
- General dialogue: emotion/tone labels as benchmark aids, not product proof.

## Lightweight Validation

```bash
python -m py_compile scripts/*.py
```

```bash
python -m pytest tests/test_validate_corpus_manifest.py tests/test_validate_gold_labels.py tests/test_evaluate_signal_outputs.py tests/test_validate_model_registry.py tests/test_validate_training_sets_registry.py tests/test_run_weak_label_baseline.py tests/test_train_text_classifier_baseline_smoke.py tests/test_validate_nlp_tools_registry.py -q
```

```bash
python scripts/check_markdown_links.py README.md docs/*.md
```

## Current Deterministic Demo Commands

```bash
python scripts/signal_engine_analyze.py --domain support data/signal_engine_2_0/sample_support.json
python scripts/signal_engine_analyze.py --domain sales data/signal_engine_2_0/sample_sales.json
python scripts/signal_engine_analyze.py --domain account_management data/signal_engine_2_0/sample_account_management.json
```

```bash
python scripts/run_signal_engine_2_0_demo.py
```

## Registry And Corpus Checks

```bash
python scripts/validate_corpus_manifest.py --path data/corpus/manifests/first_30_working_manifest.csv
python scripts/validate_gold_labels.py --path data/gold_labels.example.jsonl
python scripts/validate_model_registry.py --path data/model_registry.example.json
python scripts/validate_training_sets_registry.py --path data/training_sets_registry.example.csv
python scripts/validate_nlp_tools_registry.py --path data/nlp_tools_registry.example.json
```

Registries track candidate tools, datasets, and model families. They are not implementation proof and do not download anything.

## First Real Proof Command

First, manually place a legally safe local transcript here:

```text
data/corpus/manual_cases/NVDA_2026_Q4/raw/transcript.txt
```

Then run:

```bash
python scripts/run_weak_label_baseline.py --input data/corpus/manual_cases/NVDA_2026_Q4/raw/transcript.txt --case-id NVDA_2026_Q4 --out data/corpus/manual_cases/NVDA_2026_Q4/processed/weak_predictions.jsonl
```

The weak-label output is deterministic and review-only. It is not a final gold label file.

## NLP Research Map

- [NLP tools and research map](docs/nlp-tools-and-research-map.md)
- [Training set plan](docs/training-set-plan.md)
- [Model registry](docs/model-registry.md)
- [Benchmark matrix plan](docs/benchmark-matrix-plan.md)

Tools and datasets are tracked only. Nothing is downloaded by adding registry rows, no ML is validated, and deterministic transcript-first extraction remains the system core.

## Research Layer: Ilya Sutskever Reading List

This repo now includes a research/distillation layer that maps a public Ilya Sutskever reading-list mirror to Signal Engine 2.0 architecture, roadmap, metadata, and future feature ideas.

- Docs: [Ilya reading list research layer](docs/research/ilya_reading_list/README.md)
- Metadata: `data/research/ilya_reading_list/papers_metadata.json`
- Matrix: `data/research/ilya_reading_list/research_to_signal_engine_matrix.csv`
- CLI:

```bash
python tools/research_paper_map.py --list
python tools/research_paper_map.py --paper attention_is_all_you_need
python tools/research_paper_map.py --category attention_transformers
python tools/research_paper_map.py --signal-engine-roadmap
```

Current status: research and distillation only. This does not implement production neural models, train large systems, add paid APIs, or change deterministic Signal Engine behavior.

## Key Docs

- [First real case proof](docs/first-real-case-proof.md)
- [GitHub repo hygiene report](docs/github-repo-hygiene-report.md)
- [Branch hygiene action plan](docs/branch-hygiene-action-plan.md)
- [Default branch transition plan](docs/default-branch-transition-plan.md)
- [NLP tools and research map](docs/nlp-tools-and-research-map.md)
- [Training set plan](docs/training-set-plan.md)
- [Model registry](docs/model-registry.md)
- [Benchmark matrix plan](docs/benchmark-matrix-plan.md)
- [Transcript sectioning and labeling playbook](docs/transcript-sectioning-and-labeling-playbook.md)
- [Corpus build plan](docs/corpus-build-plan.md)
- [Ideal 30-call download list](docs/ideal-30-call-download-list.md)
