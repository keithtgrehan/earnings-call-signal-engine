# Argilla Review Workflow

Argilla is review infrastructure only. It is not canonical truth and it does not run autonomous review.

## Local Startup

Install review-only extras when using Argilla:

```bash
pip install -e ".[review]"
```

The core deterministic pipeline does not require Argilla.

Start Argilla locally using your preferred local process, then set:

```bash
export ARGILLA_API_URL=http://localhost:6900
export ARGILLA_API_KEY=<local-api-key>
export ARGILLA_WORKSPACE=default
export ARGILLA_DATASET=signal_engine_review
```

Bootstrap the dataset:

```bash
make review-bootstrap
```

The bootstrap command rejects non-local URLs by default, validates the local connection and workspace, and creates the dataset only if it is missing. To shut down, stop the local Argilla process you started. Local Argilla volumes are ignored by git.

No external LLM enrichment is part of this workflow.

## Export

```bash
python tools/export_argilla_dataset.py \
  --input-jsonl data/review/deterministic_signal_outputs.jsonl \
  --output-jsonl data/review/argilla_export.jsonl \
  --manifest-json data/review/argilla_export.manifest.json
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
  --export-manifest data/review/argilla_export.manifest.json \
  --gold-output data/gold/gold_labels.jsonl \
  --review-output data/review/canonical_reviews.jsonl
```

Import fails closed on malformed rows. Rejected and uncertain rows are preserved in canonical review output but are not promoted to gold labels.

## Dry Run

```bash
make review-dryrun
```

The dry run uses tiny deterministic fixtures and writes runtime outputs under `data/review/runtime/dryrun`, which is ignored by git. It proves export, simulated review, strict import, evaluation, analytics, SQLite persistence, and provenance events without touching canonical corpus directories.

## Review Packet Bridge

Existing labeling packets should be normalized before Argilla export instead of creating a second review system:

```bash
python tools/parse_labeling_packets.py \
  --packet path/to/human_labeling_packet.md \
  --jsonl-out data/review/runtime/packet_candidates.jsonl

python tools/export_argilla_dataset.py \
  --input-jsonl data/review/runtime/packet_candidates.jsonl \
  --output-jsonl data/review/runtime/packet_argilla_export.jsonl \
  --manifest-json data/review/runtime/packet_argilla_export.manifest.json
```

This preserves the same canonical review schema and the same guarded import path.

## Troubleshooting

- Missing `argilla`: install with `pip install -e ".[review]"`.
- Non-local URL rejected: use localhost for the review workflow unless a reviewed local tunnel is explicitly configured with `ARGILLA_ALLOW_NONLOCAL=true`.
- Missing workspace: create the workspace in local Argilla, then rerun `make review-bootstrap`.
- Dataset exists: bootstrap exits idempotently and does not recreate it.

## Evaluation

```bash
python tools/run_review_evaluation.py \
  --deterministic-jsonl data/review/deterministic_signal_outputs.jsonl

python tools/build_duckdb_analytics.py
```

The evaluator compares deterministic outputs against canonical gold labels and records the run in SQLite.
