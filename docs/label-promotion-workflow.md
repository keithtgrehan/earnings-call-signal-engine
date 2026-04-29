# Label Promotion Workflow

This workflow grows the reviewed signal dataset without turning mined candidates into automatic truth.

## Steps

1. Run `python scripts/mine_signal_label_candidates.py`.
2. Review `data/nlp_research/signal_label_candidates_review.csv`.
3. Fill `reviewer_label`, `reviewer_confidence`, `reviewer_notes`, and `accepted`.
4. Run `python scripts/promote_reviewed_label_candidates.py`.
5. Re-run the benchmark and error analysis after promotion.

## Promotion Rules

- Only rows with `accepted = true|yes|1` are eligible.
- `reviewer_label` must be one of:
  - `risk_friction`
  - `opportunity_commitment`
  - `uncertainty_hedging`
  - `neutral`
- Empty text rows are ignored.
- Duplicate IDs and duplicate normalized text are skipped conservatively.

## Boundaries

- Local support, sales, and account-management fixtures remain the primary training source.
- Loughran-McDonald can inform lexical suggestions, but it does not replace human review.
- Financial PhraseBank stays benchmark-only.
- Candidate mining creates review queues, not canonical labels.

## What To Avoid

- Do not promote rows without an explicit reviewer label.
- Do not bulk-accept mined candidates without reading them.
- Do not overwrite the seeded label dataset by hand when the promotion script can append safely.
