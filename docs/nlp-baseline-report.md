# NLP Baseline Report

- status: `insufficient_data`
- task: `signal_family`
- source_kind: `deterministic_weak_labels`
- model family: `tfidf + logistic_regression`
- interpretation boundary: research benchmark only; deterministic transcript extraction remains canonical

## Data Sources

- `data/signal_engine_2_0/fixtures/account_management_realistic.jsonl`
- `data/signal_engine_2_0/fixtures/sales_calls_realistic.jsonl`
- `data/signal_engine_2_0/fixtures/support_tickets_realistic.jsonl`
- `data/signal_engine_2_0/sample_account_management.json`
- `data/signal_engine_2_0/sample_sales.json`
- `data/signal_engine_2_0/sample_support.json`

## Weak-Label Method

- `risk_friction`: deterministic support frustration/deflection/escalation, pricing objection, competitor pressure, renewal-risk, and unresolved-issue terms
- `opportunity_commitment`: deterministic resolution, next-step, buyer-intent, owner-commitment, and expansion terms
- `uncertainty_hedging`: deterministic hedge and caution terms
- `neutral`: remaining transcript segments with no matched weak-label terms

## Label Support

| label | support |
| --- | --- |
| risk_friction | 14 |
| opportunity_commitment | 9 |
| uncertainty_hedging | 1 |
| neutral | 0 |

## Status

local weak-label corpus is too small or imbalanced for an honest 4-class benchmark split

- total_examples: `24`
- minimum_total_examples: `12`
- minimum_examples_per_class: `2`
- insufficient_labels: `uncertainty_hedging, neutral`

## Why This Is Still Useful

- It proves the repo can build a reproducible weak-label corpus from deterministic rules without inventing labels.
- It keeps the modeling workstream honest when the local corpus is too small for a credible split.
- It preserves deterministic extraction as the trustworthy path while still setting up later benchmark work.

## Limitations

- Local fixtures are intentionally tiny and architecture-focused.
- Weak labels inherit the blind spots of the deterministic rules that created them.
- No claim is made that this baseline beats deterministic extraction or generalizes to production traffic.
