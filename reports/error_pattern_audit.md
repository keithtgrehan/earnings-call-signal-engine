# Error Pattern Audit

This audit is grounded in current deterministic predictions over canonical gold labels.

## Current Bottlenecks

- Tiny mixed-provenance label set; fixture rows dominate the current benchmark.
- Opportunity terms overlap heavily with uncertainty clauses.
- Neutral operational status language can resemble risk or commitment without context.
- Guidance/outlook text needs finance-specific interpretation.

## Label Imbalance

- label_counts: `{'risk_friction': 13, 'opportunity_commitment': 15, 'uncertainty_hedging': 18, 'neutral': 11}`
- source_counts: `{'fixture': 36, 'human_reviewed': 12, 'imported_guidance': 9}`

## Remaining Confusion Pairs

- `uncertainty_hedging->opportunity_commitment`: 3
- `neutral->opportunity_commitment`: 2
- `opportunity_commitment->neutral`: 2
- `uncertainty_hedging->risk_friction`: 2
- `risk_friction->opportunity_commitment`: 1

## Representative Errors

- `risk_sales_procurement_block_001` `risk_friction->opportunity_commitment` evidence=`['procurement', 'next step']` source=`human_reviewed` text=That feels vague. Without a concrete next step, security packet, and discount range, procurement will not move this week.
- `opp_support_resolution_seed_001` `opportunity_commitment->neutral` evidence=`[]` source=`fixture` text=Thanks, the replacement order arrived this morning and I'm happy with how quickly your team solved it.
- `opp_sales_security_review_path_001` `opportunity_commitment->neutral` evidence=`[]` source=`fixture` text=the onboarding looks lighter than what we've seen before.
- `unc_support_waiting_update_001` `uncertainty_hedging->risk_friction` evidence=`['someone will reach out']` source=`fixture` text=We are still looking into it and someone will reach out later once billing has an update.
- `unc_sales_discount_signoff_001` `uncertainty_hedging->risk_friction` evidence=`['discount']` source=`fixture` text=If the discount works and security signs off
- `unc_account_if_recovery_lands_001` `uncertainty_hedging->opportunity_commitment` evidence=`['fixed', 'recovery plan']` source=`human_reviewed` text=If the recovery plan lands and the integrations are fixed
- `unc_sales_confusion_seed_001` `uncertainty_hedging->opportunity_commitment` evidence=`['implementation']` source=`fixture` text=Can you explain what this new implementation fee covers? I don't understand the difference between the two quotes.
- `unc_support_concern_seed_001` `uncertainty_hedging->opportunity_commitment` evidence=`['send']` source=`fixture` text=I'm concerned the rollback plan still hasn't been confirmed. Please send the update to [EMAIL] when you have it.
- `neut_sales_opening_full_001` `neutral->opportunity_commitment` evidence=`['pilot', 'rollout']` source=`fixture` text=Thanks for making time. I can walk through the pilot scope, rollout plan, and how teams usually evaluate the workflow.
- `neut_account_review_schedule_001` `neutral->opportunity_commitment` evidence=`['renewal review']` source=`human_reviewed` text=with a renewal review for next Tuesday.

## Fastest Path To Precision >0.55 And F1 >0.55

- Keep the accepted context-suppression rules.
- Add 43+ high-quality labels, prioritizing uncertainty/opportunity and neutral/status examples.
- Review imported guidance labels manually before making product-readiness claims.
- Avoid tuning only on fixture rows.

## Risks Of Overfitting Tiny Data

- The current improvement is large because the dataset is small and error patterns are concentrated.
- Future transcripts may introduce new wording not represented in the 57-label set.
- Source-quality subset reporting should be treated as equally important as all-label metrics.
