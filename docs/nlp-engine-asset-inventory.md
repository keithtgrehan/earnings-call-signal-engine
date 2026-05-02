# NLP Engine Asset Inventory

Current branch: `codex/aapl-first-gold-label-cycle`

This inventory separates reusable Signal Engine assets from earnings-call-specific corpus work. It is intentionally conservative: external datasets are marked unavailable unless a local loader and local reviewed source files already exist.

## Existing NLP Tools

- `src/signal_engine/`: deterministic conversation schema, domain profiles, risk/opportunity rules, privacy redaction, dataset ingestion, model registry, and baseline signal helpers.
- `scripts/signal_engine_analyze.py`: local CLI for deterministic Signal Engine 2.0 analysis with optional redaction.
- `scripts/run_text_emotion_benchmark.py`: benchmark harness for text emotion fixtures and redaction checks.
- `scripts/train_signal_baseline.py`, `scripts/train_signal_text_baseline.py`, `scripts/train_text_classifier_baseline.py`: lightweight baseline training utilities.
- `tools/run_case_pipeline.py`: one-case earnings transcript workflow for validation, weak labels, human packet generation, selected-candidate conversion, conditional evaluation, and manifest update.
- `tools/transcript_downloader/`: earnings transcript download, audit, normalization, weak labels, label validation, evaluation, distribution checks, and selected-candidate conversion.

## Existing Datasets And Manifests

- `data/signal_engine_2_0/`: in-repo support, sales, and account-management fixtures for deterministic pipeline tests.
- `data/training_sets_registry.example.csv` and `.json`: external training-set candidate registry examples.
- `data/nlp_tools_registry.example.json`: NLP tool candidate registry.
- `data/model_registry.example.json`: model candidate registry.
- `data/nlp_research/research_manifest.json`: curated research and dataset references.
- `data/research_resource_fit/public_resource_fit_manifest.json`: public-resource fit notes.
- `data/external/financial_phrasebank/`: ignored local-only intake folder.
- `data/external/loughran_mcdonald/`: ignored local-only intake folder.
- `data/external/financial_twitter_sentiment/`: ignored local-only intake folder.

## Existing Weak-Label And Evaluation Scripts

- `tools/transcript_downloader/run_corpus_analysis.py`: deterministic earnings transcript analysis and weak-label generation.
- `tools/transcript_downloader/build_gold_label_packet.py`: candidate packet generation for human review; it never writes final gold labels.
- `tools/transcript_downloader/apply_selected_gold_labels.py`: selected-candidate conversion with draft vs human-approved modes.
- `tools/transcript_downloader/apply_selected_candidates_batch.py`: batch selected-candidate conversion, defaulting to draft labels.
- `tools/transcript_downloader/audit_selected_candidates.py`: selected CSV audit before conversion.
- `tools/transcript_downloader/validate_gold_labels.py`: final gold-label validator.
- `tools/transcript_downloader/check_label_distribution.py`: label distribution and benchmark coverage checks.
- `scripts/evaluate_gold_benchmark.py`, `scripts/evaluate_label_agreement.py`, `scripts/analyze_signal_errors.py`: repo-level evaluation and error-analysis utilities.

## Missing Or Manual Dataset Loaders

- Financial PhraseBank: local importer exists; raw source files must be manually supplied after license review.
- Loughran-McDonald: local importer exists; official CSV must be manually supplied after license review.
- FiQA: reference documentation exists; no committed local loader is active.
- Financial Twitter sentiment: local setup manifest script exists; no loader is active until the source format and license posture are confirmed.
- SEC / 8-K data: intake guidance and index-fetching support exist; no raw SEC corpus is committed.
- Sales, support, renewals, and HR benchmarks: fixtures exist for deterministic behavior, but broad real-world datasets require user-owned exports, redaction, and human review.

## Earnings-Call-Specific Assets

- Transcript downloader and corpus tools under `tools/transcript_downloader/`.
- Earnings-specific labels: `guidance_revision`, `analyst_pressure`, `uncertainty`, `commitment`, `neutral`.
- Earnings call source manifests, transcript sectioning, Q&A speaker extraction, and transcript-first evidence spans.

## Reusable Assets

- Conversation schema and evidence-span contract.
- Domain adapter pattern in `src/signal_engine/domains.py`.
- Deterministic rule baseline and weak-label generation pattern.
- Human review packet workflow.
- Selected-candidate approval workflow.
- Draft vs human-approved label separation.
- Gold-label validation and conservative evaluation reporting.
- Privacy redaction utilities.

## Current Gaps

- External raw benchmark datasets are not committed and should remain local-only.
- Human-approved labels are still sparse relative to a stable benchmark target.
- Sales/support/renewals/HR domains need larger human-reviewed corpora before performance claims.
- Draft labels are useful for review operations but are not final benchmark truth.
