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
- Rights-cleared resource registry scaffold for corpus/source provenance, restricted-artifact blocking, and metadata-only source adapters.
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
- Resource registry records are required before expanding source classes, external datasets, or raw-body storage.

## 10. Roadmap

1. Expand the 25-company / 100-call corpus with legally usable transcript sources.
2. Review more earnings-call packets and grow the gold set to `100+`, then `500-1,000` labels.
3. Validate deterministic metrics on human-reviewed-only and fixture-excluded subsets.
4. Use disagreement analysis to reduce false positives and ambiguous guidance mappings.
5. Run retrieval benchmarks only after the reviewed-label gate is met.
6. Keep the public repo focused on deterministic, transcript-first evaluation rather than broad AI scope.

## 11. Rights-Cleared Corpus Readiness

The corpus strategy is rights-cleared and metadata-first. Use `configs/resource_registry.example.yml`, `schemas/resource_registry.schema.json`, and `scripts/validate_resource_registry.py` to record source tier, storage permission, commit permission, training/evaluation use, provenance, and blocked reasons.

Key docs:

- `docs/data_rights_and_corpus_policy.md`
- `docs/public_domain_and_source_terms_playbook.md`
- `docs/evaluation_claims_matrix.md`
- `docs/control_room_codex_rollout_review.md`
- `docs/corpus_500_automation_plan.md`
- `docs/source_rights_and_media_policy.md`
- `docs/audio_video_ingest_strategy.md`
- `docs/chunking_and_retrieval_object_strategy.md`
- `docs/nlp_benchmark_matrix.md`
- `docs/control_room_500_call_rollout_review.md`

External datasets and weak labels can support benchmarks and review, but they never become gold labels without human review. Restricted transcript-provider bodies must not be copied, committed, trained on, or used for evaluation claims without explicit rights.

Safe scaffold checks:

```bash
make corpus-safe-check
```

The rights-safe 500-call scaffold is documentation/config/validator infrastructure only: no raw acquisition, no production model training, and no BYOK reviewer execution has been performed. Training-readiness checks are now represented, but they fail closed unless human-reviewed gold labels, source rights, and artifact policies pass.

Current scaffold split:

- Built foundation: rights registry, restricted-artifact checks, NYSE target-universe metadata validation, source discovery queues, manual-local registration, retrieval/event-study/training-plan/BYOK validators, metadata-only adapters, and safe Make targets.
- Built pilot automation: Agent 5 NYSE 30 metadata pilot targets, source queue guardrails, manual-local path/hash batch registration, Agent 4 gold-label audit and first-100 review staging, and Agent 1 deterministic candidate pilot scaffolds.
- Scaffolded: synthetic retrieval metrics, synthetic smoke training, benchmark metadata, NLP training-source inventory, A/B and multivariate experiment design, deterministic review queues, and BYOK request/response contracts.
- Future/gated: real 500-call acquisition, raw media ingest, canonical gold repair/promotion, real training, real retrieval indexing, provider-backed review, market-data event studies, ASR/video review, and any model-quality claim.

## Cross-domain NLP safety/research

The cross-domain NLP safety work is docs/config/tests only. It adds research guardrails for finance NLP, dating-app assistive NLP, and multimodal affective cue metadata without model implementation, raw media ingestion, emotion truth claims, trading claims, or dating manipulation.

Key docs:

- `docs/research/multimodal_affective_cue_research.md`
- `docs/multimodal_audit_layer.md`
- `docs/legal/multimodal_rights_and_ai_act_guardrails.md`
- `docs/research/cross_domain_nlp_affective_finance_dating_memo.md`
- `docs/architecture/cross_domain_safe_nlp_architecture.md`
- `docs/policies/red_lines_cross_domain_nlp.md`
- `docs/evaluation/cross_domain_metrics.md`

The scope remains transcript-first and reviewer-support only: no raw audio/video ingestion, no production emotion-recognition models, no true-emotion or deception claims, no biometric identity inference, no workplace/education emotion inference, no trading/alpha/buy/sell claims, and no dating manipulation scoring.

## Portfolio / Technical Review Path

- `PORTFOLIO_README.md`
- `docs/technical_reviewer_brief.md`
- `docs/portfolio_architecture.md`
- `docs/evaluation_strategy.md`
- `docs/demo_walkthrough.md`
- `reports/demo/portfolio_demo_report.md`
- `docs/evaluation/first_50_benchmark_report.md`
