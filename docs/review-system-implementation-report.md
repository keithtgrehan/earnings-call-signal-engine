# Review System Implementation Report

## Implemented

- Canonical review schema documented in `docs/review_schema.md`.
- Deterministic Argilla JSONL export in `tools/export_argilla_dataset.py`.
- Strict Argilla review import in `tools/import_argilla_reviews.py`.
- Local SQLite operational store in `src/signal_engine/storage/sqlite_store.py`.
- SQLite initialization CLI in `tools/init_signal_engine_db.py`.
- Deterministic review evaluator in `tools/run_review_evaluation.py`.
- Local analytics report builder in `tools/build_duckdb_analytics.py`.
- Reviewer workflow and architecture docs.
- Five-transcript validation path covering NVDA, META, NFLX, SBUX, and FDX.
- Local Argilla bootstrap in `scripts/review/bootstrap_argilla.py`.
- Offline end-to-end dry run in `tools/run_review_pipeline_dryrun.py`.
- JSON schema artifacts for review exports, imports, evaluator outputs, and provenance events.

## Scaffolded Only

- Argilla server startup remains local operator responsibility; the repo bootstraps the dataset but does not ship a server or Docker dependency.
- DuckDB persistence is operational when the optional `review` extra is installed. Without that extra, markdown/CSV analytics still run and the tool gives install guidance.
- SQLite stores lifecycle and evaluation history, but no UI depends on it yet.

## Deferred

- 30-50 reviewed-call execution.
- Reviewer agreement adjudication UI.
- Statistical significance claims.
- Production ML training claims.
- Retrieval system claims.
- Market correlation proof.
- Automated transcript review.

## Deterministic Boundaries

Deterministic extraction remains canonical for candidate generation. Gold labels remain canonical for evaluation. Argilla is only a review interface. Weak labels are never auto-promoted. No LLM review, hidden enrichment, or autonomous decisioning is introduced here.

Canonical truth path:

`deterministic extraction -> review candidate -> reviewed import -> validated gold label`

Only validated `accept`, `edit`, and `relabel` rows with matching terminal states are eligible for gold output.

## Provenance Guarantees

- Exports create manifests with schema version, tool version, row counts, review IDs, and provenance IDs.
- Imports must reference exported review and provenance IDs.
- Provenance ID changes fail closed.
- Transcript paths are checked when present.
- Evidence spans are classified as `none`, `exact_mismatch`, `partial_mismatch`, `transcript_missing`, or `section_mismatch`.
- SQLite persists review records, provenance events, gold labels, and evaluation runs.

## Current Limitations

The review workflow is now technically wired, but deterministic extraction quality is still not fully proven. The benchmark is limited by label volume, label diversity, and reviewer coverage. Metrics should be treated as workflow diagnostics, not production proof.

No statistical significance, production benchmark validity, retrieval quality, or market correlation proof is claimed.

## Why Human Review Is The Bottleneck

The system can now export candidates, import reviewed rows, preserve provenance, and evaluate deterministic outputs. The missing ingredient is enough carefully reviewed evidence spans to measure false positives, false negatives, ambiguity, and class-specific failure modes.

## Path To 30-50 Reviewed Calls

1. Run deterministic extraction on the five-call validation set.
2. Export local Argilla review JSONL.
3. Review all candidates using the canonical actions.
4. Import accepted, edited, and relabeled rows through the strict importer.
5. Run review evaluation and DuckDB analytics.
6. Inspect false positives, evidence mismatches, and uncertainty rates.
7. Expand in batches of 5-10 calls until 30-50 calls have reviewed labels.

No production ML, validated benchmark significance, retrieval quality, or market relationship should be claimed before that review corpus exists.
