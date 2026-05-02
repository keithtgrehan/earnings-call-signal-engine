# General NLP Signal Engine Architecture

Signal Engine is designed as a reusable conversation intelligence foundation. The core contract is evidence-backed signal extraction from transcript text, with deterministic baselines before model training.

## Domain Adapter Pattern

Supported adapters should map domain roles and labels into a shared evidence schema:

- `earnings_calls`: analysts, executives, operator; guidance, pressure, uncertainty, commitment.
- `sales`: buyer and rep; objections, buying intent, budget pressure, next steps.
- `support`: customer and agent; severity, frustration, escalation, resolution.
- `renewals`: customer and account manager; churn risk, blockers, value realization, expansion.
- `HR`: employee/candidate and HR/manager; engagement risk, policy concern, follow-up commitment.

## Common Pipeline

```text
ingest -> normalize -> segment -> detect entities -> weak labels -> human review -> gold labels -> evaluation -> model training
```

## Reusable Labels

- `pressure`
- `uncertainty`
- `commitment`
- `performance_change`
- `escalation`
- `objection`
- `churn_risk`
- `expansion_signal`
- `sentiment`
- `neutral`

## Domain-Specific Mappings

- Earnings: `analyst_pressure`, `guidance_revision`, `uncertainty`, `commitment`.
- Sales: objections, buying intent, budget pressure, competitor pressure.
- Support: severity, frustration, escalation, directness, resolution.
- Renewals: churn risk, value realization, unresolved blockers, expansion.
- HR: engagement risk, attrition risk, policy concern, manager/HR follow-up.

## Model Strategy

1. Deterministic baseline first.
2. Lexicon features for transparent finance and conversation signals.
3. Simple sklearn baselines after enough human labels exist.
4. Transformer baselines for comparison, not as proof by themselves.
5. Embeddings/retrieval for evidence search and review acceleration.
6. Reranking for candidate prioritization.
7. Optional LLM audit only as a review aid, never as hidden ground truth.

## Safety Rules

- No diagnosis.
- No hidden-intent claims.
- No investment, trading, alpha, or stock prediction claims.
- Evidence-backed spans only.
- Raw data stays local unless explicitly approved.
- Privacy redaction before sharing artifacts.
- Human-in-the-loop review before benchmark claims.

## Benchmark Boundary

Draft labels are review operations. Final benchmark labels require explicit human approval and `human_label=true`.
