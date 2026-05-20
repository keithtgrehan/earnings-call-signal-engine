# Signal Engine

Signal Engine is a transcript-first evaluation system for turning earnings-call and other business conversations into evidence-backed signal candidates, human-review workflows, and benchmark reports.

It is not a trading system and does not claim production ML, statistical significance, or market alpha. Deterministic transcript analysis remains canonical. Weak labels, ML, retrieval, embeddings, external datasets, and multimodal work are benchmark or support layers only.

## 1. What It Is

Signal Engine ingests transcripts, preserves provenance, extracts deterministic signal candidates, routes reviewable evidence to humans, promotes only accepted labels into gold data, and reports quality through gated evaluation.

The strongest proof path is earnings-call transcripts because guidance language, analyst Q&A pressure, uncertainty, and friction can be tied to concrete transcript evidence.

## 2. Why It Matters

Generic AI summaries are hard to trust when they lack evidence, provenance, and quality gates. Signal Engine makes signal extraction reviewable and measurable:

- every candidate keeps a source and evidence trail
- weak labels are suggestions, not truth
- human-reviewed labels are the canonical truth source
- benchmark reports are gated by reviewed-label volume and provenance quality
- optional ML/retrieval layers compare against the deterministic baseline without replacing it

## 3. Architecture

```text
public/legal transcript source
  -> intake + provenance
  -> deterministic extraction
  -> weak-label suggestions
  -> human review
  -> accepted gold labels
  -> gated evaluation
  -> benchmark, retrieval, and stakeholder reports
```

Optional layers include local Argilla review infrastructure, local TF-IDF/logistic-regression benchmarking, retrieval benchmark scaffolds, source-quality reporting, and multimodal research hooks. These are explicitly benchmark/support layers.

## 4. Current Proven Capabilities

- Transcript intake for provenance-backed public or manually supplied sources.
- Source discovery and verification for high-signal earnings-call transcript URLs.
- Manual-source workflow for legally usable local transcript files.
- Safe tiered transcript acquisition workflow with robots/paywall/block safeguards.
- Deterministic signal extraction and evidence-object generation.
- Weak-label candidate generation.
- Human review packets and accepted-label promotion workflow.
- Local Argilla review workflow for transcript chunks and suggestions.
- Gold-label evaluation loop with precision, recall, and F1 reporting.
- Source-quality and fixture-excluded reporting.
- TF-IDF + Logistic Regression benchmark, gated and benchmark-only.
- Retrieval benchmark scaffold, gated until reviewed-label volume is sufficient.
- Offline portfolio demo.

## 5. Human Review Loop

Weak labels are reviewer aids only. They are never auto-promoted.

CSV/packet workflow:

```bash
make review-priority-labels
# Review data/labeling/priority_review_packet.csv or data/labeling/priority_review_packet.md.
make promote-reviewed-priority-labels
make eval-after-review
```

Local Argilla workflow:

```bash
pip install -e ".[review]"
make review-bootstrap
make review-load-transcripts
make review-upload-suggestions
make review-build-queue
REVIEWED_JSONL=/path/to/reviewed.jsonl make review-export-gold
make review-eval
```

Important docs:

- `docs/review_workflow.md`
- `docs/argilla_setup.md`
- `docs/human_review_guidelines.md`
- `docs/manual_transcript_source_workflow.md`

## 6. Evaluation Philosophy

Current validated benchmark snapshot:

- Canonical gold labels: `57`
- Deterministic precision: `0.8399`
- Deterministic recall: `0.8326`
- Deterministic F1: `0.8276`
- TF-IDF + Logistic Regression benchmark: precision `0.7332`, recall `0.7328`, F1 `0.7327`
- Label distribution: `risk_friction=13`, `opportunity_commitment=15`, `uncertainty_hedging=18`, `neutral=11`

These are promising early scores, not production claims. The label set is still small and mixed-provenance. Source-quality subset metrics and additional human-reviewed earnings-call labels matter more than the headline metric until the corpus reaches `100+` reviewed labels.

Gates:

- Local ML is benchmark-only and allowed after `>=50` valid gold labels.
- Retrieval/embedding work requires `>=100` gold labels or explicit experiment mode.
- External datasets require verified local files or safe-local metadata.
- Dataset adapters never merge external rows into gold labels automatically.
- ML, retrieval, and embeddings cannot override deterministic outputs.

## 7. Repo Structure

- `tools/`: intake, source discovery, review, evaluation, benchmark, and report scripts.
- `scripts/review/`: local Argilla review CLIs.
- `src/review/`: deterministic chunking, suggestions, queueing, export, and optional DuckDB helpers.
- `src/signal_engine/`: evaluation, datasets, deterministic baselines, and support modules.
- `data/corpus/`: corpus manifests, source templates, and metadata-backed case folders.
- `data/labeling/`: review packets and priority-review artifacts.
- `data/gold/`: canonical reviewed labels.
- `reports/`: evaluation, benchmark, review, source-quality, and demo reports.
- `docs/`: architecture, workflow, reviewer, portfolio, and evaluation documentation.

## 8. Local Setup

```bash
pip install -e .
pip install -e ".[dev]"
```

Optional review tooling:

```bash
pip install -e ".[review]"
```

Core commands:

```bash
make portfolio-demo
make eval-loop
make next-experiment
make review-priority-labels
make review-build-queue
```

High-signal source and intake flow:

```bash
make discover-high-signal-sources-query-only
make verify-high-signal-sources
make intake-high-signal-from-discovered-sources
```

Manual-source flow:

```bash
make prepare-manual-transcript-sources
make intake-manual-transcript-files
make review-after-manual-intake
```

## 9. Current Limitations

- No trading automation or investment advice.
- No production ML claim.
- No statistical-significance claim.
- No production retrieval-quality claim.
- No validated multimodal-intelligence claim.
- Human-reviewed label volume is still the bottleneck.
- Public transcript acquisition must respect robots, paywalls, login gates, and source terms.
- Raw transcript bodies and generated review/runtime artifacts should stay out of commits unless explicitly provenance-backed and intentionally committed.

## 10. Roadmap

1. Expand the 25-company / 100-call corpus with legally usable transcript sources.
2. Review more earnings-call packets and grow the gold set to `100+`, then `500-1,000` labels.
3. Validate deterministic metrics on human-reviewed-only and fixture-excluded subsets.
4. Use disagreement analysis to reduce false positives and ambiguous guidance mappings.
5. Run retrieval benchmarks only after the reviewed-label gate is met.
6. Keep the public repo focused on deterministic, transcript-first evaluation rather than broad AI scope.

## Portfolio / Technical Review Path

- `PORTFOLIO_README.md`
- `docs/technical_reviewer_brief.md`
- `docs/portfolio_architecture.md`
- `docs/evaluation_strategy.md`
- `docs/demo_walkthrough.md`
- `reports/demo/portfolio_demo_report.md`
- `docs/evaluation/first_50_benchmark_report.md`
