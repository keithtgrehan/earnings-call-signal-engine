# False Positive Clusters

Generated from current deterministic predictions over canonical gold labels.

## weak_blocker_language

- examples: `4`
- confidence: `high`
- likely_root_cause: Operational status terms can describe neutral process state rather than risk.
- recommended_refinement: Require stronger risk terms before predicting risk_friction.
- affected_labels: `{'risk_friction->opportunity_commitment': 1, 'uncertainty_hedging->risk_friction': 2, 'neutral->opportunity_commitment': 1}`
- trigger_frequency: `{'discount': 2, 'someone will reach out': 1, 'renewal': 1}`

| id | confusion | triggers | text |
| --- | --- | --- | --- |
| `risk_sales_procurement_block_001` | `risk_friction->opportunity_commitment` | `discount` | that feels vague without a concrete next step security packet and discount range procurement will not move this week |
| `unc_support_waiting_update_001` | `uncertainty_hedging->risk_friction` | `someone will reach out` | we are still looking into it and someone will reach out later once billing has an update |
| `unc_sales_discount_signoff_001` | `uncertainty_hedging->risk_friction` | `discount` | if the discount works and security signs off |
| `neut_account_review_schedule_001` | `neutral->opportunity_commitment` | `renewal` | with a renewal review for next tuesday |

## generic_positive_or_commitment

- examples: `3`
- confidence: `high`
- likely_root_cause: Generic action verbs such as send/review need stronger evidence-span requirements.
- recommended_refinement: Require actor plus action plus deadline or concrete resolution.
- affected_labels: `{'uncertainty_hedging->opportunity_commitment': 2, 'neutral->opportunity_commitment': 1}`
- trigger_frequency: `{'fixed': 1, 'recovery plan': 1, 'send': 1, 'review': 1}`

| id | confusion | triggers | text |
| --- | --- | --- | --- |
| `unc_account_if_recovery_lands_001` | `uncertainty_hedging->opportunity_commitment` | `fixed, recovery plan` | if the recovery plan lands and the integrations are fixed |
| `unc_support_concern_seed_001` | `uncertainty_hedging->opportunity_commitment` | `send` | i'm concerned the rollback plan still hasn't been confirmed please send the update to email when you have it |
| `neut_account_review_schedule_001` | `neutral->opportunity_commitment` | `review` | with a renewal review for next tuesday |

## hedge_or_conditional

- examples: `3`
- confidence: `high`
- likely_root_cause: Conditional language is competing with commercial next-step vocabulary.
- recommended_refinement: Prefer uncertainty unless explicit owner/action commitment is present.
- affected_labels: `{'uncertainty_hedging->risk_friction': 2, 'uncertainty_hedging->opportunity_commitment': 1}`
- trigger_frequency: `{'if': 2, 'once': 1}`

| id | confusion | triggers | text |
| --- | --- | --- | --- |
| `unc_support_waiting_update_001` | `uncertainty_hedging->risk_friction` | `once` | we are still looking into it and someone will reach out later once billing has an update |
| `unc_sales_discount_signoff_001` | `uncertainty_hedging->risk_friction` | `if` | if the discount works and security signs off |
| `unc_account_if_recovery_lands_001` | `uncertainty_hedging->opportunity_commitment` | `if` | if the recovery plan lands and the integrations are fixed |

## rollout_procurement_pilot

- examples: `3`
- confidence: `high`
- likely_root_cause: Lifecycle/process nouns are useful weak triggers but are not commitments by themselves.
- recommended_refinement: Suppress generic process terms under conditional or status-only contexts.
- affected_labels: `{'risk_friction->opportunity_commitment': 1, 'uncertainty_hedging->opportunity_commitment': 1, 'neutral->opportunity_commitment': 1}`
- trigger_frequency: `{'procurement': 1, 'implementation': 1, 'rollout': 1, 'pilot': 1}`

| id | confusion | triggers | text |
| --- | --- | --- | --- |
| `risk_sales_procurement_block_001` | `risk_friction->opportunity_commitment` | `procurement` | that feels vague without a concrete next step security packet and discount range procurement will not move this week |
| `unc_sales_confusion_seed_001` | `uncertainty_hedging->opportunity_commitment` | `implementation` | can you explain what this new implementation fee covers i don't understand the difference between the two quotes |
| `neut_sales_opening_full_001` | `neutral->opportunity_commitment` | `rollout, pilot` | thanks for making time i can walk through the pilot scope rollout plan and how teams usually evaluate the workflow |

## low_evidence_or_other

- examples: `2`
- confidence: `medium`
- likely_root_cause: The deterministic rule either had no evidence term or a sparse ambiguous span.
- recommended_refinement: Send examples to manual review and strengthen evidence extraction.
- affected_labels: `{'opportunity_commitment->neutral': 2}`
- trigger_frequency: `{}`

| id | confusion | triggers | text |
| --- | --- | --- | --- |
| `opp_support_resolution_seed_001` | `opportunity_commitment->neutral` | `` | thanks the replacement order arrived this morning and i'm happy with how quickly your team solved it |
| `opp_sales_security_review_path_001` | `opportunity_commitment->neutral` | `` | the onboarding looks lighter than what we've seen before |
