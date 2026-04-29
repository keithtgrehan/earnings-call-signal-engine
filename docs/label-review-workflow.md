# Label Review Workflow

## Purpose

This workflow prepares the seeded `signal_family` label set for a second reviewer pass without altering the original dataset.

## Files

- source labels: `data/nlp_research/human_reviewed_signal_labels.jsonl`
- review packet CSV: `data/nlp_research/review_packets/signal_labels_review_packet.csv`
- review packet Markdown: `data/nlp_research/review_packets/signal_labels_review_packet.md`
- normalized second-review template: `data/nlp_research/second_review_template.csv`
- second-review priority queue: `data/nlp_research/second_review_priority_queue.csv`
- second-review priority guide: `docs/second-review-priority.md`
- agreement status: `data/nlp_research/label_agreement_status.json`
- agreement report: `docs/label-agreement-status.md`

## Steps

1. Run `python scripts/build_label_review_packet.py`
2. Start with the priority queue in `data/nlp_research/second_review_priority_queue.csv`
3. Share the CSV or Markdown packet with a second reviewer
4. Fill only:
   - `reviewer_label`
   - `reviewer_confidence`
   - `reviewer_notes`
5. Normalize the reviewed CSV with `python scripts/import_second_review_labels.py`
6. Run `python scripts/evaluate_label_agreement.py`

## Allowed Labels

- `risk_friction`
- `opportunity_commitment`
- `uncertainty_hedging`
- `neutral`

## Boundaries

- do not edit the original `human_reviewed_signal_labels.jsonl`
- do not invent reviewer labels to make agreement look better
- if the second reviewer has not filled any labels yet, agreement should stay in a blocked state

## What Counts As Progress

- a completed second-review CSV with explicit reviewer labels
- a reproducible agreement report
- disagreement rows that can be reviewed openly rather than hidden
