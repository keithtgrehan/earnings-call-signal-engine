# Label Promotion Status

This workflow promotes accepted candidate rows into the reviewed label dataset only after explicit human review.

- status: `blocked_no_accepted_rows`
- input_review_csv: `data/nlp_research/signal_label_candidates_review.csv`
- label_dataset_path: `data/nlp_research/human_reviewed_signal_labels.jsonl`
- accepted_rows: `0`
- promoted_rows: `0`
- duplicate_rows_skipped: `0`

## Blocked Status

- No candidate rows were marked accepted yet.
- This is expected until a reviewer completes part of the candidate review CSV.
