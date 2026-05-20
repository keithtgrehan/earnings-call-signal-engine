# DuckDB Analytics

`tools/build_duckdb_analytics.py` creates local review analytics from JSONL/CSV artifacts. It is deterministic and does not call external services.

DuckDB is an optional review extra:

```bash
pip install -e ".[review]"
```

When the `duckdb` Python package is available, the script creates a local `.duckdb` database and persists summary tables. When it is not installed, the script produces markdown/CSV summaries and prints install guidance if DuckDB is explicitly required.

## Inputs

- `data/review/canonical_reviews.jsonl`
- `data/gold/gold_labels.jsonl`
- `reports/review_evaluation_metrics.json`
- optional CSV review rows

## Outputs

- `reports/duckdb_review_analytics.md`
- optional `.duckdb` runtime database
- optional CSV summary

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

Runtime `.duckdb` files are local artifacts and are ignored by git.
