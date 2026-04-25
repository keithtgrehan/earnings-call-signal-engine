# Final Portfolio Case Study

## 1. Problem

Business conversations are hard to review consistently when the source material is long, messy, and operationally mixed. A support escalation, a pricing objection, or a renewal-risk warning can be easy to miss when the reviewer only has a raw transcript or a broad summary.

## 2. Why Generic AI Summaries Are Not Enough

Generic summaries often compress the conversation into a smooth narrative, but they usually do not show:

- which exact signal was detected
- which evidence snippet supported it
- what action a reviewer should take next
- whether the output is safe to trust without deeper inspection

Signal Engine 2.0 is built to answer those questions directly.

## 3. System Architecture

Signal Engine 2.0 is transcript-first and deterministic by default:

1. transcript or conversation JSON is loaded
2. optional deterministic PII redaction runs before analysis
3. domain-specific deterministic features extract reviewable cues
4. evidence-backed JSON output is produced
5. optional benchmark or multimodal sidecars remain secondary to the transcript

The canonical output is still the transcript-backed deterministic result, not a black-box score.

## 4. Example Output

Example case:

- domain: `support`
- conversation type: realistic synthetic billing escalation
- privacy handling: deterministic redaction replaced a synthetic email and phone number before analysis

Detected output:

- `support_low_directness`
- `support_deflection`
- `support_frustration`
- `support_escalation_risk`
- `support_low_resolution_clarity`

Evidence snippets:

- “Billing is still reviewing it, so please check the help center article for now...”
- “I'm frustrated that invoice 8842 still shows the wrong total...”
- “...if this slips again we will escalate the dispute.”

Recommended next action:

- route to a human reviewer or team lead
- confirm billing ownership
- respond with a dated remediation plan
- treat the dispute language as an escalation cue, not as a certainty claim about intent

Why this output is useful:

- it is inspectable
- it preserves evidence
- it supports redaction-aware review
- it gives a reviewer a concrete next step instead of a broad abstract summary

## 5. Evaluation Status

Transcript benchmark status:

- human-reviewed labeled dataset: `48` examples
- class counts:
  - `risk_friction`: `12`
  - `opportunity_commitment`: `13`
  - `uncertainty_hedging`: `12`
  - `neutral`: `11`
- evaluation split: `32` train / `16` held-out test examples
- deterministic rules: accuracy `0.5000`, macro F1 `0.4048`
- TF-IDF + LogisticRegression classifier: accuracy `0.5000`, macro F1 `0.5000`

Interpretation:

- this is an early labeled benchmark, not statistical proof
- the classifier is a research benchmark only
- deterministic rules remain canonical unless a stronger benchmark proves otherwise

Multimodal status:

- multimodal pilot cases seeded: `10`
- transcript-only seeds: `5`
- ready-for-audio cases: `3`
- ready-for-video cases: `2`
- complete aligned transcript+audio+video cases: `0`
- measured multimodal lift: not available yet
- second-review agreement status: blocked until reviewer labels are added
- audio pilot asset status: blocked until approved aligned audio clips are added

## 6. What Works Now

- transcript-first deterministic signal extraction
- evidence snippets attached to detected signals
- optional deterministic PII redaction
- a small human-reviewable label set for first benchmark work
- automated reviewer packet generation and agreement scaffolding
- a reproducible transcript-only benchmark
- a bounded multimodal pilot scaffold with explicit blockers
- a one-command proof refresh path via `make first-proof-refresh`

## 7. What Remains Roadmap

- larger and more diverse labeled transcript sets
- aligned transcript+audio or transcript+video pilot media
- real multimodal lift measurement
- optional ASR, diarization, and richer audio/video sidecars
- broader model benchmarking beyond the current lightweight classifier

## 8. Why This Is Relevant For Solutions Engineering / AI Systems Roles

This project shows practical AI systems work rather than prompt-only prototyping:

- translating an ambiguous workflow into auditable schemas and outputs
- preserving clear product boundaries and safety constraints
- building deterministic and model-based paths side by side without conflating them
- creating evaluation surfaces before making strong claims
- documenting limitations honestly for technical and non-technical reviewers

## Boundary Note

This system does not claim truth detection, lie detection, hidden-intent detection, psychological diagnosis, or emotion certainty. Audio and video remain optional review cues, and transcript-backed deterministic output remains the source of truth.
