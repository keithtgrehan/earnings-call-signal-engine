# Argilla Review Workflow

Argilla is review infrastructure only. It is not canonical truth and it does not run autonomous review.

## Local Startup

Run Argilla locally according to the project's local environment. Exported JSONL from this repo can be loaded into a local Argilla dataset with the fields and metadata preserved by `tools/export_argilla_dataset.py`.

No external LLM enrichment is part of this workflow.

## Export

```bash
python tools/export_argilla_dataset.py \
  --input-jsonl data/review/deterministic_signal_outputs.jsonl \
  --output-jsonl data/review/argilla_export.jsonl
```

The export preserves:

- provenance ID
- case ID
- evidence text
- evidence hints
- transcript references
- source URL
- deterministic confidence

## Review

Reviewers choose one action only:

- `accept`
- `reject`
- `edit`
- `relabel`
- `uncertain`

Edits and relabels should preserve why the original deterministic output was insufficient.

## Import

```bash
python tools/import_argilla_reviews.py \
  --input-jsonl data/review/argilla_reviewed.jsonl \
  --gold-output data/gold/gold_labels.jsonl \
  --review-output data/review/canonical_reviews.jsonl
```

Import fails closed on malformed rows. Rejected and uncertain rows are preserved in canonical review output but are not promoted to gold labels.

## Evaluation

```bash
python tools/run_review_evaluation.py \
  --deterministic-jsonl data/review/deterministic_signal_outputs.jsonl

python tools/build_duckdb_analytics.py
```

The evaluator compares deterministic outputs against canonical gold labels and records the run in SQLite.
