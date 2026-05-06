# Signal Engine

Transcript-first deterministic earnings-call signal engine with gated evaluation, label review, NLP asset registry, optional dataset adapters, and optional embedding benchmarks.

Signal Engine is an evaluation-ready research/proof repo, not a trading system. The deterministic system remains the canonical source of truth. ML, embeddings, retrieval, external datasets, and multimodal assets are optional benchmark layers only.

## 1. What This Is

This repo turns earnings-call and conversation transcripts into evidence-backed signal candidates, then evaluates those candidates against canonical gold labels. The strongest proof path is earnings-call transcripts because guidance language, analyst Q&A, uncertainty, and friction can be tied to concrete evidence spans.

The repo also contains broader scaffolding for support, sales, account-management, NLP asset discovery, Ilya reading-list research synthesis, pilot corpus ingestion, and retrieval-ready schemas. Those layers support the roadmap; they are not product proof by themselves.

## 2. What Works Now

- Deterministic transcript analysis and signal extraction scaffolds.
- Label discovery, recovery, normalization, and import into `data/gold/gold_labels.jsonl`.
- Reviewed-label validation with non-blocking handling when no accepted reviewed-batch rows exist.
- One-command evaluation loop and first-50 benchmark report.
- Next-best-action report with explicit experiment gates.
- Local ML smoke baseline once gold labels are `>=50`.
- NLP asset registry for finance lexicons, datasets, retrieval tools, audio tools, and multimodal references.
- Dataset adapters for local-only comparison, with no auto-download.
- Embedding benchmark harness, gated and benchmark-only.
- Pilot corpus manifests, representative samples, retrieval schema, and validation tests.
- Ilya Sutskever reading-list research assets and Signal Engine roadmap synthesis.

## 3. Current Measurable Proof

- Canonical gold labels: `57`
- Deterministic precision: `0.3205`
- Deterministic recall: `0.4499`
- Deterministic F1: `0.3743`
- Label distribution: `risk_friction=13`, `opportunity_commitment=15`, `uncertainty_hedging=18`, `neutral=11`
- Interpretation: recall is higher than precision, so the system currently over-detects signals. The next quality target is precision improvement through false-positive reduction.
- Full-suite validation after the rebase passed with `342` tests.

Known caveats:

- Imported labels have mixed provenance.
- Some guidance labels were mapped conservatively into the four-label taxonomy.
- `reviewed_labels.csv` / reviewed-batch files currently have no accepted review decisions to promote.
- Metrics are a measurable baseline, not statistical proof.

## 4. What Is Gated

- Local ML is allowed only after `>=50` valid gold labels and remains benchmark-only.
- Embeddings require `>=100` gold labels or explicit retrieval experiment mode.
- External datasets require verified local files or a `safe_local` asset flag.
- Rerankers require an embedding baseline first.
- Long-context review requires completed evaluation first.
- Dataset adapters never merge external rows into gold labels automatically.
- Embeddings and ML cannot override deterministic outputs.

## 5. How To Run

```bash
python tools/run_evaluation_loop.py
python tools/run_next_experiment.py || true
python tools/run_embedding_benchmark.py || true
python tools/run_retrieval_benchmark.py || true
```

```bash
make eval-loop
make next-experiment
make embedding-benchmark
make demo
```

Useful registry and research commands:

```bash
python tools/nlp_asset_map.py --validate
python tools/nlp_asset_map.py --priority high
python tools/research_paper_map.py --validate-full-asset
python tools/research_paper_map.py --signal-engine-roadmap
```

Pilot corpus checks:

```bash
PYTHONPATH=src python scripts/validate_pilot_corpus.py
python scripts/build_signal_retrieval_index.py
```

## 6. What This Does NOT Prove

- No market alpha.
- No trading automation.
- No production ML.
- No statistical significance.
- No production retrieval quality claim.
- No long-context benchmark claim.
- No validated multimodal intelligence.
- No proof that external datasets are legally usable without manual review.
- No claim that research-paper assets are implemented neural systems.

## 7. Roadmap

1. Add source-quality metadata to every imported label: `label_source`, `source_file`, `import_method`, `provenance_quality`, and `requires_manual_review`.
2. Evaluate filtered subsets such as `human_reviewed_only`, `guidance_mapped_only`, and `fixture_excluded`.
3. Reduce false positives in deterministic rules, especially neutral and uncertainty cases.
4. Complete the manual reviewed-label workflow and promote accepted rows only.
5. Grow the gold set to `100+` labels, then run the embedding benchmark explicitly.
6. Keep pilot corpus manifests, representative samples, retrieval schemas, and tiny proof artifacts committed; keep bulky generated/raw assets ignored.
7. Merge this proof branch into `main` only after validation is green, then make `main` the clean public proof branch.

Key docs:

- `docs/case_study.md`
- `docs/product_one_pager.md`
- `docs/demo_script.md`
- `docs/architecture_simple.md`
- `docs/evaluation/first_50_benchmark_report.md`
- `reports/next_best_actions.md`
- `reports/label_import_summary.md`
- `reports/demo/analyst_report_LLY_2025_Q2_call08.md`
- `docs/evaluation/source_quality_filtering_plan.md`
- `docs/pilot-corpus.md`
- `docs/nlp_assets/README.md`
- `docs/research/ilya_reading_list/README.md`
