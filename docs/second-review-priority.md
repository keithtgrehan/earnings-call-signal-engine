# Second-Review Priority

The current queue in `data/nlp_research/second_review_priority_queue.csv` focuses reviewer time on the highest-value rows first.

## Prioritization Logic

- both systems wrong
- classifier-only or rules-only wins
- ambiguous or low-confidence cases
- neutral examples that still need false-positive control
- candidate gold-holdout rows

## Current Status

- queue size: `16`
- reviewer fields remain blank by design
- this queue does not replace the full packet; it simply narrows the first reviewer pass to the most informative rows

## How To Use It

1. review this queue before the full second-review template
2. fill reviewer label and confidence fields
3. rerun `python scripts/evaluate_label_agreement.py`
4. use agreement plus error analysis to promote or demote holdout candidates
