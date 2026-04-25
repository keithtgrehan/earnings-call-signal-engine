# Signal Error Analysis

This is an early error-analysis pass on a small labeled set, not statistical proof.
Deterministic rules remain canonical.
Classifier variants are exploratory benchmark aids only.

## Dataset And Evaluation Context

- dataset_path: `/Users/keith/Documents/New project/earnings-call-signal-engine-support-qa/data/nlp_research/human_reviewed_signal_labels.jsonl`
- predictions_path: `/Users/keith/Documents/New project/earnings-call-signal-engine-support-qa/data/nlp_research/transcript_baseline_predictions.jsonl`
- dataset_size: `48`
- evaluation_scope: `train_test_split`
- canonical_system: `deterministic_rules`

## Headline Error Counts

- deterministic_rule_errors: `8`
- classifier_errors: `7`
- both_wrong: `3`
- classifier_only_correct: `5`
- rules_only_correct: `4`
- ambiguous_or_low_confidence: `10`

## Baseline Comparison Snapshot

| system | accuracy | macro_f1 | weighted_f1 |
| --- | --- | --- | --- |
| majority_baseline | 0.2500 | 0.1000 | 0.1000 |
| deterministic_rules | 0.5000 | 0.4048 | 0.4048 |
| tfidf_logreg_unigram | 0.3125 | 0.3269 | 0.3269 |
| tfidf_logreg_bigram | 0.4375 | 0.4611 | 0.4611 |
| tfidf_logreg_unigram_balanced | 0.3750 | 0.3857 | 0.3857 |
| tfidf_logreg_bigram_balanced | 0.5000 | 0.5000 | 0.5000 |
| tfidf_linear_svc_unigram_balanced | 0.4375 | 0.4504 | 0.4504 |
| tfidf_linear_svc_bigram_balanced | 0.5625 | 0.5706 | 0.5706 |

## What The Current Errors Suggest

- the strongest current rule weakness is uncertainty and neutral overfire, especially when operational terms look like commitment cues
- the classifier helps on some neutral and hedge cases, but still misses clean friction turns
- both-wrong examples are the highest-value second-review candidates

## Recommended Actions

| action | count |
| --- | --- |
| needs_second_reviewer | 11 |
| tighten_lexicon_term | 9 |
| benchmark_only_no_label_change | 4 |
| improve_neutral_examples | 4 |
| review_conditionals_and_hedges | 4 |
| hold_for_gold_set_review | 3 |
| no_action_clear_ok | 1 |

## What Not To Conclude

- This does not prove model superiority.
- This does not prove generalization.
- This does not prove that confidence equals correctness.

## Next Review Steps

- review the highest-priority rows in `data/nlp_research/signal_error_analysis.csv`
- send both-wrong and low-confidence cases into second review
- tighten neutral and hedge coverage before making stronger benchmark claims
