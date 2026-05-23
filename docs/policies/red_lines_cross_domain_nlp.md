# Red Lines for Cross-Domain NLP

Status: policy guardrail for research/config/test scope only.

All cross-domain NLP work must stay within observable cues only and candidate/reviewer-support only outputs. There is no source-rights bypass: unknown, restricted, scraped, non-consented, or unregistered sources must fail closed.

## Forbidden outputs

The system must not output or imply:

- this person is lying
- this person loves you
- emotional vulnerability scoring
- workplace/education emotion inference
- biometric identity inference
- sensitive trait inference
- trading signal claims
- source-rights bypass
- relationship manipulation suggestions
- unsupported statistical significance
- deception detection
- mental-health diagnosis
- universal emotion truth claims

## Finance red lines

- no buy/sell recommendations
- no alpha claims
- no live execution
- no causal market claim without sufficient reviewed evidence and study design
- no automatic promotion of machine labels to gold labels
- no unsupported statistical significance

## Dating-app and relationship red lines

- no attraction prediction
- no emotional vulnerability scoring
- no claims that a person loves the user
- no claims that a person is lying
- no attachment-style inference without explicit consent and safe scope
- no relationship manipulation suggestions
- no sensitive trait inference
- no non-consented third-party profiling

## Affective cue red lines

- no true emotion inference
- no universal emotion truth claims
- no deception detection
- no mental-health diagnosis
- no biometric identity inference
- no workplace/education emotion inference
- no body-language truth claims

## Required safe language

Use:

- observable cues only
- candidate/reviewer-support only
- evidence-backed candidate
- reviewer context
- not canonical
- no source-rights bypass

Block:

- truth claims about internal emotion
- personality or vulnerability scores
- deception or manipulation scores
- workplace, education, health, identity, trading, or relationship-control conclusions
