# DuckDB Analytics

`tools/build_duckdb_analytics.py` creates local review analytics from JSONL/CSV artifacts. It is deterministic and does not call external services.

The script is DuckDB-compatible, but it does not add DuckDB as a required dependency. When the `duckdb` Python package is available, the report records that availability. When it is not installed, the script uses a standard-library fallback and still produces the same markdown summary shape.

## Inputs

- `data/review/canonical_reviews.jsonl`
- `data/gold/gold_labels.jsonl`
- `reports/review_evaluation_metrics.json`
- optional CSV review rows

## Outputs

- `reports/duckdb_review_analytics.md`

## Analytics Covered

- TP, FP, and FN from the deterministic review evaluator
- direction mismatch
- evidence mismatch
- section mismatch
- unresolved ambiguity
- reviewer action counts
- reviewer throughput
- uncertainty rate
- corpus composition by transcript section

## Boundaries

This layer is analytics only. It does not create labels, edit labels, run models, or promote review decisions. It is meant to help reviewers see where deterministic extraction and reviewer guidance need tightening.
