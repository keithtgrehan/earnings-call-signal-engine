# Hero Output

## Case

Redacted support escalation review from `data/signal_engine_2_0/fixtures/support_tickets_realistic.jsonl`

## Input Context

A customer contacts support about an incorrect invoice total, a delayed credit, and a prior failed resolution. The conversation also contains synthetic email and phone details that are redacted before analysis.

## System Output

- domain: `support`
- conversation_id: `support_billing_escalation_realistic_001`
- canonical path: `text_first_offline`
- detected risk flags:
  - `support_low_directness`
  - `support_deflection`
  - `support_frustration`
  - `support_escalation_risk`
  - `support_low_resolution_clarity`
- opportunity flags:
  - none

## Detected Signals

### Frustration

- score: `0.75`
- why it was detected:
  - the customer explicitly says they are frustrated
  - the unresolved credit and failed resolution language reinforces the operational problem

### Deflection

- score: `0.6667`
- why it was detected:
  - the agent points the customer to a help-center article while billing is still “reviewing it”
  - the reply does not answer the date or ownership question directly

### Escalation Risk

- score: `0.6708`
- why it was detected:
  - the customer says they will escalate the dispute if the issue slips again

### Low Resolution Clarity

- score: `0.0`
- why it was detected:
  - the transcript does not contain a clear dated resolution commitment

## Evidence Snippets

- frustration:
  - “I’m frustrated that invoice 8842 still shows the wrong total...”
- deflection:
  - “Billing is still reviewing it, so please check the help center article for now...”
- escalation risk:
  - “...if this slips again we will escalate the dispute.”

## Recommended Next Action

- assign a billing owner and publish a dated resolution commitment
- stop routing the customer back to generic documentation
- review whether the duplicated charge and slow follow-up create refund or dispute exposure

## Why This Matters

- it is more useful than a broad negative-summary label
- a reviewer can see exactly which turns created the risk
- the output is structured enough for QA, escalation routing, or follow-up workflow design

## Redaction Note

PII redaction was enabled for this case. The output records only redaction counts and hashes, not raw personal details.

## Boundaries

- this output does not claim to know the customer’s internal state
- it does not diagnose intent or deception
- it does not prove the billing team is at fault
- it surfaces review cues and evidence that a human operator can verify quickly
