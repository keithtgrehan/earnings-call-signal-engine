# Signal Engine

Signal Engine turns long-form business conversations into structured, evidence-backed signals using deterministic NLP workflows, evaluation gates, and optional AI augmentation.

Signal Engine is an evaluation-ready research/proof repo, not a trading system. The deterministic transcript-first system remains the canonical source of truth. ML, embeddings, retrieval, external datasets, and multimodal assets are optional benchmark layers only.

## Quick Demo

```bash
make demo
```

Expected proof artifacts:

- `reports/demo/`
- `docs/demo_script.md`
- `docs/case_study.md`
- `docs/product_one_pager.md`

Human-review commands:

```bash
make review-priority-labels
make promote-reviewed-priority-labels
make eval-after-review
```

## What It Does

Signal Engine turns earnings-call and conversation transcripts into evidence-backed signal candidates, then evaluates those candidates against canonical gold labels. The strongest proof path is earnings-call transcripts because guidance language, analyst Q&A pressure, uncertainty, and friction can be tied to concrete evidence spans.

The repo also contains scaffolding for label recovery, source-quality filtering, deterministic-vs-ML benchmarking, retrieval-readiness checks, NLP asset discovery, and research synthesis. Those layers support the roadmap; they are not product proof by themselves.

## Why It Matters

Long-form business transcripts are slow to review and easy to interpret inconsistently. Signal Engine reduces review time by surfacing candidate evidence spans, keeping deterministic explanations visible, and forcing every benchmark through repeatable gold-label evaluation.

## What Works Now

- Deterministic transcript analysis and signal extraction scaffolds.
- Label discovery, recovery, normalization, and import into `data/gold/gold_labels.jsonl`.
- Reviewed-label validation with non-blocking handling when no accepted reviewed-batch rows exist.
- One-command evaluation loop and first-50 benchmark report.
- Source-quality filtering and metric comparison across provenance subsets.
- Next-best-action report with explicit experiment gates.
- Local TF-IDF + Logistic Regression benchmark once gold labels are `>=50`.
- NLP asset registry for finance lexicons, datasets, retrieval tools, audio tools, and multimodal references.
- Dataset adapters for local-only comparison, with no auto-download.
- Embedding and retrieval benchmark harnesses, gated and benchmark-only.
- Pilot corpus manifests, representative samples, retrieval schemas, and validation tests.
- Priority-call review packet generation for growing human-reviewed labels toward the next benchmark gate.
- Ilya Sutskever reading-list research assets and Signal Engine roadmap synthesis.

## Current Measurable Proof

- Canonical gold labels: `57`
- Deterministic precision: `0.8399`
- Deterministic recall: `0.8326`
- Deterministic F1: `0.8276`
- TF-IDF + Logistic Regression benchmark: precision `0.7332`, recall `0.7328`, F1 `0.7327`
- Label distribution: `risk_friction=13`, `opportunity_commitment=15`, `uncertainty_hedging=18`, `neutral=11`

The metric jump after deterministic rule refinement is promising, but `57` labels is still a small mixed-provenance benchmark. Source-quality subset metrics and new human-reviewed earnings-call labels matter more than the headline metric until the gold set reaches `100+` reviewed labels.

Known caveats:

- Imported labels have mixed provenance.
- Some guidance labels were mapped conservatively into the four-label taxonomy.
- `reviewed_labels.csv` / reviewed-batch files currently have no accepted review decisions to promote.
- Metrics are a measurable baseline, not statistical proof.
- Source-quality subset metrics should be treated as the more trustworthy validation lens until more human-reviewed labels exist.

## Human Review Workflow

Weak labels are suggestions only. Keith reviews packet rows manually, marks each row as `accept`, `reject`, or `unclear`, and only accepted rows are promoted into canonical gold labels.

```bash
make review-priority-labels
# Review data/labeling/priority_review_packet.csv or data/labeling/priority_review_packet.md.
make promote-reviewed-priority-labels
make eval-after-review
```

Important paths:

- `data/labeling/priority_review_packet.csv`
- `data/labeling/priority_review_packet.md`
- `reports/gold_label_growth_status.md`
- `reports/final_priority_review_validation.md`

## High-Signal Transcript Intake

The high-signal intake tool prepares provenance-backed transcript folders for the 25-company benchmark set. It uses configured public sources where available, creates manual-provenance placeholders when a transcript is missing, and never creates gold labels.

```bash
python tools/intake_high_signal_transcripts.py \
  --years 2024 2025 2026 \
  --quarters Q1 Q2 Q3 Q4 \
  --output-root data/corpus/high_signal_cases \
  --max-cases-per-ticker 4 \
  --dry-run
```

See `docs/high_signal_transcript_intake.md`.

## High-Signal Source Discovery

Source discovery finds and validates candidate public transcript URLs before intake downloads anything. It writes `data/corpus/high_signal_source_urls.csv` for `tools/intake_high_signal_transcripts.py --source-url-file`, plus auditable candidate evidence in `data/corpus/high_signal_source_candidates.json`.

```bash
make discover-high-signal-sources-query-only
# user/API supplies search results or candidate URLs
make verify-high-signal-sources
make intake-high-signal-from-discovered-sources
```

Discovery rejects paywall, login, captcha, blocked, and robots-disallowed pages. Intake downloads/parses verified public sources, and human review promotes labels later. No transcripts or gold labels are auto-promoted by discovery.

See `docs/high_signal_source_discovery.md`.

## How To Run

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

## Architecture

Input transcripts flow through deterministic NLP and signal extraction, then into evidence objects, gold-label evaluation, reports, and optional benchmark layers. Deterministic outputs remain canonical; ML, retrieval, embeddings, and external datasets are comparison layers that cannot override deterministic truth.

## What Is Gated / Benchmark-Only

- Local ML is benchmark-only and allowed only after `>=50` valid gold labels.
- Embeddings require `>=100` gold labels or explicit retrieval experiment mode.
- Retrieval is review/search scaffolding only until validated on a larger human-reviewed set.
- External datasets require verified local files or a `safe_local` asset flag.
- Rerankers require an embedding baseline first.
- Long-context review requires completed evaluation first.
- Dataset adapters never merge external rows into gold labels automatically.
- Multimodal work remains unvalidated unless proven separately.

## What This Does Not Claim

- No trading automation.
- No market alpha.
- No production ML claim.
- No statistical significance claim.
- No validated multimodal intelligence claim.
- No production retrieval quality claim.
- No proof that external datasets are legally usable without manual review.
- No claim that research-paper assets are implemented neural systems.

## Research / Roadmap

Near-term roadmap:

1. Review the Priority 1 earnings-call packet and grow the gold set to `100+` high-quality labels.
2. Validate the metric jump on human-reviewed and fixture-excluded subsets.
3. Reduce any remaining false positives in neutral, uncertainty, and guidance-language cases.
4. Run retrieval benchmarks only after the label gate is met or explicit retrieval experiment mode is enabled.
5. Keep pilot corpus manifests, representative samples, retrieval schemas, and tiny proof artifacts committed; keep bulky generated/raw assets ignored.

Research assets:

- NLP asset registry maps finance lexicons, public datasets, retrieval tools, audio tools, and multimodal resources to Signal Engine use cases.
- Ilya Sutskever reading-list material is distilled into roadmap and architecture implications, but it is research/distillation rather than implemented neural modeling.

## Key Docs

- `docs/case_study.md`
- `docs/product_one_pager.md`
- `docs/demo_script.md`
- `docs/architecture_simple.md`
- `docs/evaluation/first_50_benchmark_report.md`
- `reports/next_best_actions.md`
- `reports/demo/analyst_report_LLY_2025_Q2_call08.md`
- `data/labeling/priority_review_packet.md`
- `reports/call_review_inventory.md`
- `reports/transcript_download_plan.md`
- `reports/metric_jump_validation.md`
- `docs/high_signal_transcript_intake.md`
- `docs/evaluation/source_quality_filtering_plan.md`
- `docs/pilot-corpus.md`
- `docs/nlp_assets/README.md`
- `docs/research/ilya_reading_list/README.md`
