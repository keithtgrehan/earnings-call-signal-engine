# Review Validation Report

- input: `data/labeling/reviewed_next_batch.csv`
- valid_for_gold_update: `False`
- total_rows: `0`
- reviewed_rows: `0`
- accepted_rows: `0`
- accepted_gold_labels: `0`
- rejected_rows: `0`
- unclear_rows: `0`
- skipped_rows: `0`
- unreviewed_rows: `0`
- invalid_rows: `1`

## Errors

- reviewed batch not found: data/labeling/reviewed_next_batch.csv

Only rows with `review_decision` of `accept` or `edit_label` and a valid `final_label` are eligible for gold labels.
