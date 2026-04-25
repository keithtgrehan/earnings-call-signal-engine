# Transcript Baseline Benchmark

This is an early labeled benchmark, not statistical proof.
The classifier is a research benchmark only.
Deterministic rules remain canonical unless a larger and independently reviewed benchmark proves otherwise.

## Dataset

- path: `data/nlp_research/human_reviewed_signal_labels.jsonl`
- dataset_size: `48`

| label | support |
| --- | --- |
| risk_friction | 12 |
| opportunity_commitment | 13 |
| uncertainty_hedging | 12 |
| neutral | 11 |

## Historical Context

- The earlier first-proof report compared deterministic rules with a single TF-IDF + LogisticRegression classifier. This refreshed report adds a majority baseline and multiple exploratory variants.

## Evaluation Setup

- split_strategy: `train_test_split`
- selected_classifier: `tfidf_linear_svc_bigram_balanced`
- canonical_system: `deterministic_rules`
- evaluation_set_size: `16`
- warning: small benchmark; treat exploratory variants as benchmark aids only

## Headline Results

| system | type | accuracy | macro_f1 | weighted_f1 |
| --- | --- | --- | --- | --- |
| majority_baseline | baseline | 0.2500 | 0.1000 | 0.1000 |
| deterministic_rules | rules | 0.5000 | 0.4048 | 0.4048 |
| tfidf_linear_svc_bigram_balanced | classifier | 0.5625 | 0.5706 | 0.5706 |

See `docs/signal-error-analysis.md` for failure-mode review and `docs/gold-holdout-set-guide.md` for holdout discipline.

## Exploratory Model Variant Comparison

| system | type | accuracy | macro_f1 | weighted_f1 |
| --- | --- | --- | --- | --- |
| majority_baseline | baseline | 0.2500 | 0.1000 | 0.1000 |
| deterministic_rules | rules | 0.5000 | 0.4048 | 0.4048 |
| tfidf_logreg_unigram | classifier | 0.3125 | 0.3269 | 0.3269 |
| tfidf_logreg_bigram | classifier | 0.4375 | 0.4611 | 0.4611 |
| tfidf_logreg_unigram_balanced | classifier | 0.3750 | 0.3857 | 0.3857 |
| tfidf_logreg_bigram_balanced | classifier | 0.5000 | 0.5000 | 0.5000 |
| tfidf_linear_svc_unigram_balanced | classifier | 0.4375 | 0.4504 | 0.4504 |
| tfidf_linear_svc_bigram_balanced | classifier | 0.5625 | 0.5706 | 0.5706 |

## Selected Classifier Per-Class Metrics

| label | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| risk_friction | 0.6667 | 0.5000 | 0.5714 | 4 |
| opportunity_commitment | 0.4000 | 0.5000 | 0.4444 | 4 |
| uncertainty_hedging | 0.5000 | 0.7500 | 0.6000 | 4 |
| neutral | 1.0000 | 0.5000 | 0.6667 | 4 |

## Deterministic Rules Per-Class Metrics

| label | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| risk_friction | 0.5000 | 1.0000 | 0.6667 | 4 |
| opportunity_commitment | 0.6000 | 0.7500 | 0.6667 | 4 |
| uncertainty_hedging | 0.0000 | 0.0000 | 0.0000 | 4 |
| neutral | 0.3333 | 0.2500 | 0.2857 | 4 |

## Selected Classifier Confusion Matrix

| true \ predicted | risk_friction | opportunity_commitment | uncertainty_hedging | neutral |
| --- | --- | --- | --- | --- |
| risk_friction | 2 | 2 | 0 | 0 |
| opportunity_commitment | 0 | 2 | 2 | 0 |
| uncertainty_hedging | 0 | 1 | 3 | 0 |
| neutral | 1 | 0 | 1 | 2 |

## Deterministic Rules Confusion Matrix

| true \ predicted | risk_friction | opportunity_commitment | uncertainty_hedging | neutral |
| --- | --- | --- | --- | --- |
| risk_friction | 4 | 0 | 0 | 0 |
| opportunity_commitment | 0 | 3 | 0 | 1 |
| uncertainty_hedging | 2 | 1 | 0 | 1 |
| neutral | 2 | 1 | 0 | 1 |

## Train/Test IDs

- train_ids: `opp_account_expand_realistic_001, risk_support_anger_seed_001, neut_sales_status_full_001, opp_account_confirm_owners_001, unc_sales_unknown_after_pilot_001, risk_sales_procurement_block_001, opp_support_resolution_seed_001, neut_sales_opening_thanks_001, risk_support_billing_delay_001, opp_account_followthrough_seed_001, unc_support_concern_seed_001, risk_sales_pricing_objection_001, unc_account_expansion_realistic_001, neut_account_status_intro_001, unc_account_if_recovery_lands_001, neut_sales_acknowledgement_001, risk_account_reduce_seats_001, opp_sales_pilot_interest_001, opp_sales_plan_commitment_001, unc_support_waiting_update_001, opp_sales_security_packet_001, risk_support_escalation_001, neut_sales_opening_full_001, risk_support_dispute_001, unc_sales_details_later_001, unc_sales_confusion_seed_001, opp_account_expand_support_001, unc_sales_security_review_001, neut_sales_legal_status_001, risk_support_help_center_001, neut_account_review_schedule_001, opp_account_named_owners_001`
- test_ids: `neut_sales_status_procurement_001, risk_account_vendor_risk_001, opp_sales_security_review_path_001, unc_account_rollout_condition_001, neut_account_status_full_001, risk_account_unresolved_001, opp_account_recovery_plan_001, opp_sales_procurement_path_001, opp_account_own_recovery_001, neut_account_status_meeting_001, unc_sales_probably_001, unc_support_confusion_seed_001, risk_support_deflection_001, risk_support_refund_delay_001, neut_account_status_agenda_001, unc_sales_discount_signoff_001`

## Limitations

- The labeled set is small, hand-seeded, and drawn from committed local fixtures only.
- Many seeded labels were chosen with help from deterministic lexicons, so this benchmark is not independent proof of model superiority.
- The majority baseline and exploratory variants improve context, not certainty.
- Gold holdout candidates and second-review prioritization are now scaffolded, but final gold status still requires second reviewer input.
