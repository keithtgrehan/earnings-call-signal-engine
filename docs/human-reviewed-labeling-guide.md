# Human-Reviewed Labeling Guide

## Purpose

This guide defines the first small `signal_family` label set for Signal Engine 2.0.

It is intentionally conservative. The goal is to create a human-reviewable benchmark seed, not a claim of production-grade annotation quality.

## Labels

### `risk_friction`

Use when the text clearly shows:

- complaint, frustration, or escalation pressure
- unresolved issue language
- pricing or procurement blockers
- downgrade, churn, dispute, or competitor pressure

Positive examples:

- “The failed resolution has been open since Monday...”
- “...we may cut seats, delay the renewal, or look at another vendor.”

Do not use when:

- the text is only a schedule update
- the text is only hedged or conditional without clear friction

### `opportunity_commitment`

Use when the text clearly shows:

- concrete next-step commitments
- ownership with dates or named follow-up
- expansion, pilot, or procurement-forward motion
- confirmed resolution or acceptable recovery

Positive examples:

- “I own the action items and will send a recovery plan by Friday...”
- “We appreciate the follow-through and that works for our renewal review.”

Do not use when:

- the language is vague, hedged, or non-committal
- the only positive cue is tone without an operational commitment

### `uncertainty_hedging`

Use when the text clearly shows:

- visibility gaps
- conditional language
- hedging words such as `may`, `might`, `probably`, `if`, `not sure`
- explicit confusion or lack of clarity about current status

Positive examples:

- “If the discount works and security signs off...”
- “I still do not know what happens after the pilot.”

Do not use when:

- the text is purely procedural
- the text is clearly a complaint or escalation and friction is the stronger signal

### `neutral`

Use when the text is mostly:

- operational scheduling
- acknowledgements
- document or meeting logistics
- status framing without clear friction, commitment, or uncertainty

Positive examples:

- “the meeting starts at 09:00 CET”
- “Thanks for making time.”

Do not use when:

- the text includes meaningful blocker, complaint, commitment, or hedge language

## Exclusion Rules

- Do not label raw personal data. Redact first if needed.
- Do not infer hidden intent, internal emotion certainty, deception, or body-language meaning.
- Do not label based on speaker role alone.
- Do not let a single weak cue override a stronger clearer cue in the same snippet.

## Ambiguous Cases

When a snippet contains both a positive and a cautious cue:

1. prefer the operationally dominant signal
2. if a clause is cleanly separable, split it into two snippets
3. if the text still feels mixed, choose the safer less-strong label and record the ambiguity in `notes`

## How To Label Neutral

Neutral is not “everything else.” It should be used for:

- schedule and logistics
- acknowledgements
- process or artifact references

Avoid labeling a snippet neutral if it contains:

- unresolved issue language
- future-conditional language
- explicit commitment or ownership
- escalation or objection language

## Future Review Process

For future label additions:

1. confirm the text comes from committed local fixtures or approved datasets
2. redact PII before saving labels
3. write a short rationale
4. capture evidence terms
5. prefer conservative labels over clever labels
6. review class balance before using the dataset in any benchmark
