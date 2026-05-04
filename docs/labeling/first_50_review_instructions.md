# First 50 Gold Label Review Instructions

This is the fastest path to the first real gold labels.

## Start Review

Run:

```bash
python tools/review_next_batch.py --reviewer Keith
```

The tool reads:

```text
data/labeling/next_review_batch.csv
```

It writes:

```text
data/labeling/reviewed_next_batch.csv
```

If `reviewed_next_batch.csv` already exists, the tool resumes from the first unreviewed row and creates a timestamped backup before saving.

## Keyboard Shortcuts

- `a`: accept the weak label.
- `r`: reject / no signal.
- `e`: edit the final label.
- `u`: unclear.
- `s`: skip.
- `q`: save and quit.

Valid final labels:

- `risk_friction`
- `opportunity_commitment`
- `uncertainty_hedging`
- `neutral`

## Practical Review Rules

- Accept only when the weak label is clearly correct.
- Edit when the text is useful but the weak label is wrong.
- Reject boilerplate, generic disclaimers, admin text, and unusable fragments.
- Use unclear when deciding would take more than a quick read.
- Skip when you want to postpone without deciding.

Weak labels never become gold unless you explicitly accept or edit them.

## Validate

Run:

```bash
python tools/validate_reviewed_batch.py
```

Expected output:

- reviewed rows
- accepted rows
- rejected rows
- unclear rows
- skipped rows
- invalid rows
- whether the file is valid for gold update

The report is written to:

```text
docs/labeling/review_validation_report.md
```

Fix any validation errors before updating gold labels.

## Update Gold Labels

Run:

```bash
python tools/update_gold_from_review.py
```

This validates the reviewed file, imports reviewed labels, builds `data/gold/gold_labels.jsonl`, checks coverage, evaluates only when gates allow it, and trains only when the existing training gate allows it.

Expected outputs:

- `data/labeling/reviewed_labels.csv`
- `data/gold/gold_labels.jsonl`
- `data/gold/rejected_labels.jsonl`
- `data/gold/unclear_labels.jsonl`
- `docs/labeling/gold_label_status.md`
- `docs/evaluation/benchmark_status.md`
- `docs/model_eval/text_signal_model_card.md`

## What Done Looks Like

For the first pass, done means:

- 50 rows have review decisions.
- Validation passes.
- Accepted rows appear in `data/gold/gold_labels.jsonl`.
- Rejected and unclear rows are tracked but excluded from gold.
- The model card still says training is gated unless at least 50 accepted gold labels exist.

## After The First 50

Review the next batch until there are at least 150 clean gold labels. Watch label balance: a useful benchmark needs coverage across `risk_friction`, `opportunity_commitment`, `uncertainty_hedging`, and `neutral`.

Training remains gated. Do not treat the first baseline as meaningful until the gold dataset is large enough and the benchmark report says the evaluation is valid.
