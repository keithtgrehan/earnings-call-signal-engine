# Signal Engine 2.0 Polished Examples

These examples are recruiter-, buyer-, and reviewer-facing summaries of deterministic Signal Engine 2.0 outputs. They are meant to show how the system surfaces structured, evidence-backed signals from messy transcripts without claiming hidden intent certainty, truth detection, or black-box emotional truth.

## 1. Support Review Example

Short input context:
A customer contacts support about a billing error, says the issue has already been raised twice, and shares synthetic contact details so the case can be traced.

Structured output summary:
- domain: `support`
- detected review state: unresolved billing issue with escalation risk
- output style: deterministic flags, evidence snippets, and redaction-aware metadata

Detected signals:
- support deflection
- support frustration
- support escalation risk
- weak resolution clarity

Evidence snippets:
- "Refund timing sits with another team, so I can't change it here."
- "I've already asked twice and the problem is still open."
- "I'm pretty frustrated at this point."

Recommended next action:
Route to a human reviewer or team lead, confirm billing ownership, and provide a concrete resolution or timeline instead of another handoff.

Redaction note:
When `--redact-pii` is enabled, synthetic email and phone details are replaced before analysis and only hash-based redaction records are retained in metadata.

Why the output is useful:
It gives a reviewer a compact, auditable explanation of why the conversation suggests service risk, without relying on a broad summary or unsupported certainty claims.

## 2. Sales Review Example

Short input context:
A prospective buyer is interested in moving forward, but raises pricing pressure, compares the product to a competitor, and leaves the next step weaker than ideal.

Structured output summary:
- domain: `sales`
- detected review state: active deal motion with pricing and competitive pressure
- output style: deterministic opportunity/risk flags with transcript evidence

Detected signals:
- sales pricing risk
- sales competitor pressure
- buyer intent
- weak next-step discipline

Evidence snippets:
- "The seat cost still feels high for where we are."
- "We're also comparing this against Intercom."
- "Let's try to regroup sometime next week."

Recommended next action:
Tighten the next-step commitment, answer the pricing objection directly, and equip the rep with a concrete competitor comparison for the next review.

Redaction note:
No raw PII should be exposed in polished output examples; examples here use role-level context and short evidence snippets only.

Why the output is useful:
It helps a manager or buyer see what was detected, why it was detected, and what requires review next, without pretending to predict closed-won outcomes from the transcript alone.
