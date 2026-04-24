# Signal Engine 2.0 Demo Pack

## What this demonstrates

- deterministic conversation intelligence across support, sales, and account management
- transcript-first analysis with evidence-backed signals
- plain-English review outputs that stay grounded in specific turns
- no LLM dependency, no external API dependency, and no UI dependency

## Demo 1 — Support QA

Input summary:

A customer follows up on an overdue refund tied to an open ticket, the agent deflects to billing and a FAQ, the issue remains unresolved, and the customer threatens escalation and a charge dispute.

Top signals:

- `support_deflection`
- `support_low_directness`
- `support_frustration`
- `support_escalation_risk`

Evidence snippets:

- "Refund timing sits with another team, so please refer to the billing FAQ for now..."
- "That still doesn't answer the question. I need a real date..."
- "...if this is still unresolved today I'll escalate it to your manager and dispute the charge."
- "We are still looking into it and someone will reach out later..."

Business story:

This would have flagged a likely escalation before a supervisor had to read the full thread. For a support QA lead, it narrows review to a vague, deflective exchange with clear customer frustration and unresolved ownership.

## Demo 2 — Sales Call Review

Input summary:

A prospect expresses interest in a pilot, raises pricing concerns, compares the product to Zendesk and Intercom, and signals procurement involvement if the next step goes well.

Top signals:

- `sales_buyer_intent`
- `sales_pricing_risk`
- `sales_objection_pressure`
- `sales_competitor_pressure`
- `sales_next_step_defined`

Evidence snippets:

- "We're interested in a pilot next month if the security review goes well..."
- "The seat cost feels expensive versus Zendesk..."
- "...the team is also comparing you to Intercom."
- "I can send a pilot plan, pricing options, and a proposal by Tuesday..."

Business story:

This would have saved a sales manager from manually skimming the call just to learn the deal is real but price-sensitive. It focuses follow-up on discount strategy, competitor pressure, and whether the rep left the call with a concrete next step.

## Demo 3 — Account Management / CS

Input summary:

An existing customer is approaching renewal with unresolved onboarding issues, warns that seats may be cut or the vendor replaced, but also suggests possible expansion if stability improves.

Top signals:

- `account_renewal_risk`
- `account_churn_risk`
- `account_unresolved_issues`
- `account_negative_sentiment`
- `account_expansion_opportunity`

Evidence snippets:

- "Our renewal is in about 45 days, and we're still dealing with two unresolved onboarding issues..."
- "...we may cut seats, delay the renewal, or look at another vendor."
- "If the rollout stabilizes this quarter, we may add the support team and upgrade..."
- "I own the action items and will send a recovery plan by Friday..."

Business story:

This would have improved customer-success review focus by showing both downside risk and upside potential in the same call. A CS leader can quickly see that the account needs recovery execution now, but still has expansion value if the open issues are closed.

## How to run

```bash
python scripts/signal_engine_analyze.py --domain support data/signal_engine_2_0/sample_support.json
python scripts/signal_engine_analyze.py --domain sales data/signal_engine_2_0/sample_sales.json
python scripts/signal_engine_analyze.py --domain account_management data/signal_engine_2_0/sample_account_management.json
```

Demo JSON artifacts in this pack:

- `demo/signal_engine_2_0/support_demo_output.json`
- `demo/signal_engine_2_0/sales_demo_output.json`
- `demo/signal_engine_2_0/account_management_demo_output.json`

## What this is not

- not a black-box AI score
- not a replacement for managers
- not live call automation
- not legal or compliance advice
