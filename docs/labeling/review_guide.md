# Gold Label Review Guide

This review step turns weak candidate labels into human gold labels. Weak labels are suggestions only. A row becomes gold only when the reviewer explicitly chooses `accept` or `edit_label` and provides a valid final label.

## Decision Rules

- `accept`: the weak label is correct and the text span is useful as a training example.
- `reject`: no real signal, generic boilerplate, legal disclaimer, admin text, duplicate junk, or unusable span.
- `edit_label`: the text is useful, but the weak label is wrong.
- `unclear`: the reviewer cannot decide quickly. Do not force a gold label.
- `skip`: postpone without deciding.

Accepted and edited rows are eligible for `data/gold/gold_labels.jsonl`. Rejected, unclear, skipped, and unreviewed rows are excluded from gold.

## Labels

### `risk_friction`

Use for real business risk, constraint, analyst pushback, margin pressure, demand concern, supply issue, pricing concern, or execution concern.

Examples:
- A customer says renewal is blocked by unresolved onboarding issues.
- Management describes margin pressure, supply constraints, demand weakness, or pricing risk.
- An analyst challenges execution, guidance, pricing, or demand assumptions.

Do not use for generic cautionary language with no concrete business issue.

### `opportunity_commitment`

Use for management commitment, concrete plan, raised outlook, expansion, or strong forward-looking opportunity tied to business impact.

Examples:
- A leader commits to named owners, dates, or next steps.
- Management raises outlook or describes expansion with a business impact.
- A sales buyer commits to a pilot, procurement path, or implementation plan.

Do not use for vague optimism without a concrete action or business implication.

### `uncertainty_hedging`

Use for business-relevant uncertainty, conditional guidance, or uncertainty about demand, supply, pricing, tariffs, margins, or timing.

Examples:
- Management says demand depends on timing, tariff outcomes, supply availability, or customer budgets.
- A buyer is unsure whether procurement, pricing, pilot scope, or timing will work.
- A support or success case has unresolved timing or ownership uncertainty.

Reject generic legal disclaimers, safe-harbor language, and broad “results may differ” statements unless the text includes a specific business uncertainty.

### `neutral`

Use for factual, administrative, or non-signal content that is useful as a negative training example.

Examples:
- Operator instructions.
- Factual transitions or greetings.
- Plain status text with no risk, opportunity, uncertainty, or commitment.

Neutral is still a deliberate gold label. Use it when the text is clean and helpful as a negative example, not when the span is junk.

## What To Reject

- Safe-harbor or legal disclaimer language without a specific business signal.
- Boilerplate call openings, closing remarks, or webcast instructions.
- Text fragments too short to judge.
- Duplicated junk rows.
- PII-heavy or broken spans that should not train the model.
- Weak labels that look plausible only because of generic words like “may,” “could,” or “expect.”

## What To Mark Unclear

- The span seems meaningful but the business context is missing.
- Two labels seem equally plausible and a quick decision is not possible.
- The text may be a signal, but the span is too truncated to label confidently.

Use `unclear` instead of guessing. The goal is fewer, cleaner gold labels.

## Boilerplate Handling

Most boilerplate should be rejected. Legal disclaimers are especially risky because they over-teach `uncertainty_hedging`. Keep boilerplate only if it is clean neutral text and useful as a negative example.

## Avoid Over-Labeling Uncertainty

Do not label every hedge word as `uncertainty_hedging`. The uncertainty must matter to a business outcome: demand, supply, pricing, tariffs, margin, timing, procurement, renewal, escalation, or execution.

## First Targets

- First target: 50 reviewed rows.
- Second target: 150 reviewed rows.
- Third target: 500 reviewed rows.

Training remains gated. The first real baseline requires at least 50 accepted gold labels, and a serious benchmark requires substantially more coverage across labels and domains.
