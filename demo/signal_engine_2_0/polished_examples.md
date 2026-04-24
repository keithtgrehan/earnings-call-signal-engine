# Signal Engine 2.0 Polished Examples

## 1. Support QA

Input summary:
Support customer reports a billing error, unresolved refund timing, and escalating frustration.

Detected signals:
- support low directness
- support deflection
- support frustration
- support escalation risk

Evidence snippets:
- "Refund timing sits with another team..."
- "I'm honestly pretty frustrated..."
- "I'll escalate it to your manager..."

Business interpretation:
Useful for surfacing unresolved support interactions where the response quality and escalation risk matter more than a generic sentiment score.

Limitation:
This is deterministic transcript analysis, not customer intent certainty or deception detection.

## 2. Sales Call Review

Input summary:
Prospective buyer signals pilot interest but raises pricing pressure, competitor comparison, and weak next-step concerns.

Detected signals:
- sales pricing risk
- sales objection pressure
- sales competitor pressure
- sales buyer intent

Evidence snippets:
- "The seat cost feels expensive versus Zendesk..."
- "The team is also comparing you to Intercom."
- "We can bring procurement in next week."

Business interpretation:
Useful for identifying whether a deal is real but blocked, and whether the rep created enough clarity to progress.

Limitation:
The output does not estimate win probability from hidden variables outside the transcript.

## 3. Account Management / CS

Input summary:
Renewal is close, onboarding issues remain open, and expansion stays possible if recovery succeeds.

Detected signals:
- account churn risk
- account renewal risk
- account unresolved issues
- account expansion opportunity

Evidence snippets:
- "Our renewal is in about 45 days..."
- "We may cut seats, delay the renewal..."
- "We may still expand analytics seats..."

Business interpretation:
Useful for separating account risk from upside so a team can prioritize save motions and expansion motions together.

Limitation:
This is a transcript-backed workflow signal, not a contractual forecast.

## 4. Text Emotion Benchmark

Input summary:
A tiny handcrafted benchmark checks whether deterministic emotion labeling and reporting infrastructure behave correctly.

Detected signals:
- label prediction with evidence terms
- confusion matrix counts
- macro F1
- per-label precision/recall/F1

Evidence snippets:
- "urgent"
- "frustrated"
- "thank you"

Business interpretation:
Useful as harness validation for future optional text emotion comparisons without making models canonical.

Limitation:
Tiny handcrafted fixtures are not production proof and do not validate psychological diagnosis.

## 5. PII Redaction

Input summary:
Support transcript includes synthetic email and phone details before analysis.

Detected signals:
- email redacted to `[EMAIL]`
- phone redacted to `[PHONE]`
- hash-only redaction records stored

Evidence snippets:
- output preserves the redacted sentence shape
- metadata records redaction summary only

Business interpretation:
Useful for privacy-aware benchmarking and demos where evidence should remain readable without leaking raw identifiers.

Limitation:
This is a deterministic fallback redactor, not a full compliance or entity-resolution system.
