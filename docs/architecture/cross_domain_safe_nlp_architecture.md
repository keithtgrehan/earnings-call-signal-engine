# Cross-Domain Safe NLP Architecture

Status: architecture guardrail only. This does not implement ingestion, training, provider execution, production models, trading logic, or relationship-scoring logic.

## Layered architecture

```text
rights/consent gate
  -> PII minimization
  -> dataset registry
  -> deterministic baseline
  -> candidate classifier
  -> evidence object store
  -> retrieval layer
  -> BYOK reviewer layer
  -> multimodal metadata layer
  -> evaluation gates
  -> output safety guardrails
```

## Rights/consent gate

The consent gate blocks unknown, unregistered, scraped, restricted, or non-consented sources. Finance sources require source-rights records. Dating-app data requires opt-in consent, user ownership or clear authorization, privacy scope, and deletion/export expectations. Multimodal media requires rights-cleared registration and allowed-feature scope.

## PII minimization

PII minimization happens before dataset expansion, retrieval, reviewer prompts, exports, or logs. The system should preserve enough provenance for review while redacting unnecessary identifiers, message bodies, personal contact details, and sensitive attributes.

## Dataset registry

Every model, dataset, lexicon, benchmark, and placeholder resource must declare source type, license status, allowed use, training permission, benchmark-only status, risk level, and relevance. External datasets are benchmark-only by default and never become gold labels without human adjudication.

## Deterministic baseline

The deterministic baseline remains canonical in Signal Engine. It extracts transcript-backed finance cues and evidence spans. In dating-app assistive NLP, deterministic or rules-first baselines should capture harassment, toxicity, consent/safety, and pressure-language patterns before any candidate classifier is trusted.

## Candidate classifier

Candidate classifiers are optional and bounded. They can propose labels for review or benchmark comparison, but they cannot override deterministic extraction, make sensitive claims, produce trading claims, or infer true emotion/deception.

## Evidence object store

The evidence object store preserves source references, spans, timestamps, cue metadata, provenance, rights status, and reviewer state. It must not store raw dating data, raw media, provider outputs, embeddings, vector DBs, or bulky artifacts unless a separate policy explicitly allows it.

## Retrieval layer

The retrieval layer operates over evidence objects and approved chunks. Retrieval quality is measured with recall@k, MRR, nDCG, latency, and cost. Retrieval cannot be used to hide weak extraction or invent unsupported claims.

## BYOK reviewer layer

The BYOK reviewer layer summarizes fixed evidence bundles with user-owned keys when configured. It is reviewer-support only, must preserve citations, and must pass unsupported-claim checks. BYOK reviewer outputs are not canonical labels.

## Multimodal metadata layer

The multimodal metadata layer is optional, rights-cleared, flagged-window-only, and reviewer-support only. It may record observable cue metadata such as pauses, overlap, confidence, action-unit metadata, or pose metadata. It must not infer true emotion, deception, mental health, biometric identity, workplace/education emotion, or relationship manipulation.

## Evaluation gates

Evaluation gates block claims unless the right evidence exists:

- finance extraction: precision, recall, macro F1, direction accuracy
- evidence quality: exact span match, partial span match, invalid citation rate
- retrieval: recall@k, MRR, nDCG, latency, cost
- reviewer layer: faithfulness, unsupported claim rate, citation quality
- dating safety: harassment recall, pressure-language precision, false-positive rate
- privacy: redaction pass rate, deletion/export success
- affective metadata: macro F1, calibration/ECE, abstain rate, reviewer usefulness

## Output safety guardrails

Outputs must be evidence-backed, scoped, and free of red-line claims. The system blocks deception detection, mental-health diagnosis, biometric identity inference, sensitive trait inference, workplace/education emotion inference, trading signal claims, relationship manipulation suggestions, unsupported statistical significance, and universal emotion truth claims.
