# Corpus Build Plan

Signal Engine 2.0 should earn credibility by moving from polished demos to a small, reviewable earnings-call corpus with explicit provenance, manual labels, and evidence spans. The canonical path remains transcript-first deterministic extraction; audio, video, retrieval, and model review are later experiments only.

## Scope

- First target: 30 manually confirmed earnings calls split across guidance-change candidates, stable controls, and messy ambiguous calls.
- Later target: 100-150 calls after the first 30-call process has stable manifests, labels, evidence review, and error analysis.
- Current scaffold: example manifests, example labels, validators, evaluator, and error-analysis template.
- Not included: transcript downloads, paid APIs, scraping, production ML, statistical claims, market-reaction correlation, or heavy generated artifacts.

## Manual Download Workflow

1. Pick a case from `docs/ideal-30-call-download-list.md`.
2. Confirm source rights and availability manually through company investor relations, SEC EDGAR, exchange sites, or licensed transcript vendors.
3. Record the case in `data/corpus_manifest.example.csv` or a future real manifest copy.
4. Save only permitted transcript text to a local raw transcript path.
5. Update `transcript_status` from `placeholder` to `downloaded`, then to `parsed` or `validated` only after checks pass.
6. Add weak or manual labels in JSONL format using the schema in `data/gold_labels.example.jsonl`.
7. Run validators before promoting any case into an evaluation set.

## Manifest Promotion Rules

- `candidate`: source has been identified but not manually confirmed.
- `placeholder`: example row or planning row only; not evaluation-ready.
- `downloaded`: transcript exists locally and source rights have been checked.
- `parsed`: deterministic transcript parsing completed without known section errors.
- `validated`: reviewer confirmed source, sections, speaker roles, and evidence span quality.
- `blocked`: source access, licensing, transcript quality, or provenance is insufficient.

## No-Claim Boundaries

- Synthetic support/sales/account data does not prove product value.
- A few earnings-call demos do not prove repeatability.
- The current scaffold does not establish statistical significance.
- Deterministic signal counts are not market predictions.
- Retrieval, embeddings, and long-context review should wait until deterministic evaluation and error analysis are repeatable.

## Recommended File Flow

- Planning manifest: `data/corpus_manifest.example.csv`
- JSON planning manifest: `data/corpus_manifest.example.json`
- Label examples: `data/gold_labels.example.jsonl`
- Future raw transcripts: `data/corpus/raw/transcripts/`
- Future prediction JSONL: `data/corpus/evaluation/predictions/`
- Future evaluation reports: `data/corpus/evaluation/reports/`
