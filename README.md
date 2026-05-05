# Signal Engine

Transcript-first deterministic earnings-call signal engine with gated evaluation, label review, NLP asset registry, optional dataset adapters, and optional embedding benchmarks.

Signal Engine is an evaluation-ready research/proof repo, not a trading system. The deterministic system remains canonical truth; ML, external datasets, and embeddings are benchmark layers only.

The strongest proof path is earnings-call transcripts because public-company sources, explicit guidance language, analyst Q&A, and evidence-span review create a credible route to repeatable evaluation. Broader domains are supported or scaffolded where the same transcript-first pattern applies: customer support, sales calls, account management, churn risk, and general dialogue tone/emotion benchmarks.

This repo does not claim production ML, statistical significance, market alpha, market-reaction proof, production retrieval, or validated multimodal intelligence.

## Current Proof State

- Canonical gold labels: `57`
- Deterministic evaluation now runs against `data/gold/gold_labels.jsonl`.
- Baseline precision: `0.3205`
- Baseline recall: `0.4499`
- Baseline F1: `0.3743`
- Current interpretation: recall is higher than precision, so the deterministic system currently over-detects signals and needs false-positive reduction.
- Local ML is allowed by gate because gold labels are now `>=50`, but any ML run is benchmark-only.
- Embeddings remain gated until `>=100` gold labels or explicit retrieval experiment mode.
- Full validation passed most recently with `342` tests passing.

## What Works Now

- Deterministic transcript analysis and signal extraction scaffolds for evidence-backed review.
- Label discovery, recovery, normalization, and import into canonical gold labels.
- Gold-label validation and label coverage reporting.
- One-command evaluation loop.
- First-50 benchmark report and next-best-action report.
- NLP asset registry for datasets, lexicons, benchmarks, retrieval tools, audio tools, and multimodal references.
- Safe experiment runner with gating.
- Dataset adapters for local-only comparison.
- Embedding benchmark harness, gated and benchmark-only.
- Earnings-call corpus manifest validation.
- SEC 8-K metadata-only intake.
- Manual corpus case setup.
- Deterministic weak-label keyword baseline for local `.txt` transcripts.
- First 3 earnings-call intake cases: `NVDA_2026_Q4`, `META_2025_Q4`, and `AMZN_2025_Q4`.
- Repo validation and documentation checks.

## Gated Or Not Proven

- Local ML baseline requires `>=50` gold labels and must be compared honestly against the deterministic baseline.
- Embeddings require `>=100` gold labels or explicit retrieval experiment mode.
- External datasets require verified local files and are never silently downloaded by benchmark scripts.
- Rerankers require an embedding baseline first.
- Long-context review requires completed evaluation.
- No alpha, statistical, production ML, product-readiness, retrieval quality, long-context benchmark, or market prediction claims.
- No committed raw transcripts, restricted datasets, model weights, audio, video, or paid API outputs.

## Quickstart Proof Commands

```bash
python tools/run_evaluation_loop.py
python tools/run_next_experiment.py || true
python tools/run_embedding_benchmark.py || true
```

```bash
make eval-loop
make next-experiment
make embedding-benchmark
```

If `tools/run_evaluation_loop.py` reports that no accepted reviewed-batch rows were found, that is non-blocking for the current proof state. It means `data/labeling/reviewed_next_batch.csv` has not supplied new accepted review rows, so the loop continues with the existing canonical gold labels.

## Recommended Next Steps

- Clean source-quality metadata for imported labels.
- Compare `all_labels` against `human_reviewed_only` once source filtering exists.
- Improve false-positive rules to raise precision.
- Complete the manual reviewed-label workflow.
- Grow the canonical gold set to `100+` labels.
- Then run the embedding benchmark as a gated retrieval experiment.

## Scaffolded Only

- Sales, support, and account-management use cases beyond the deterministic demo/sample layer.
- Public dataset and model candidates.
- Embeddings, rerankers, and long-context model candidates.
- Optional local sklearn training scaffold.
- Emotion/tone dataset references.

Scaffolded means tracked, documented, or locally runnable as a smoke check. It does not mean validated, production-ready, or trained.

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

## Research Layer: Full Paper Asset

The full paper asset extends the reading-list layer with a legal/public source registry, local ignored cache workflow, parsed metadata digests, deep paper briefs, a Signal Engine synthesis, feature backlog, and Keith reading plan.

- Source registry: `data/research/ilya_reading_list/source_registry.json`
- Extracted metadata/digests: `data/research/ilya_reading_list/extracted/`
- Deep briefs: `docs/research/ilya_reading_list/papers/`
- Full synthesis: [Signal Engine 2.0 full synthesis](docs/research/ilya_reading_list/signal_engine_2_0_full_synthesis.md)
- Feature backlog: `data/research/ilya_reading_list/signal_engine_feature_backlog.csv`
- Reading plan: [Keith reading plan](docs/research/ilya_reading_list/keith_reading_plan.md)

```bash
python tools/research_paper_map.py --parsed-status
python tools/research_paper_map.py --brief attention_is_all_you_need
python tools/research_paper_map.py --feature-backlog
python tools/research_paper_map.py --reading-plan
python tools/research_paper_map.py --validate-full-asset
```

Raw PDFs/HTML are cached only under ignored local paths. Full raw source text is not committed because redistribution rights vary. Parsed status is explicit per paper: `full_text_parsed`, `abstract_only`, `source_unavailable`, or `citation_only`.

## NLP Assets and Dataset Registry

Signal Engine 2.0 also tracks NLP datasets, lexicons, benchmarks, retrieval tools, privacy tools, ASR/audio references, and multimodal resources in a dedicated asset registry.

- Registry: `data/nlp_assets/asset_registry.json`
- CSV export: `data/nlp_assets/asset_registry.csv`
- Docs: [NLP assets registry](docs/nlp_assets/README.md)
- Scaling plan: [Signal Engine NLP asset scaling plan](docs/nlp_assets/signal_engine_scaling_plan.md)

```bash
python tools/nlp_asset_map.py --list
python tools/nlp_asset_map.py --category finance
python tools/nlp_asset_map.py --downloaded
python tools/nlp_asset_map.py --manual-required
python tools/nlp_asset_map.py --signal-engine-area weak_labeling
python tools/nlp_asset_map.py --priority high
python tools/nlp_asset_map.py --validate
```

Safe download tooling only caches small public metadata/reference files under ignored local paths. Raw datasets, model weights, gated datasets, non-commercial corpora, and license-restricted assets require manual review and are not committed. This layer prepares benchmarking, weak labeling, retrieval, supervised training, and future multimodal evaluation without changing deterministic pipeline behavior.

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
