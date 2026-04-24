# Multimodal Evaluation Protocol

## Purpose

Evaluate whether optional audio or video review cues improve reviewer usefulness beyond the transcript-only deterministic baseline.

## Labels

- uncertainty
- hedging
- guidance change
- analyst pressure
- evasive answer
- reassurance
- contradiction
- sentiment shift
- escalation risk

## Baselines

- transcript-first deterministic review
- transcript + audio sidecar
- transcript + audio + video sidecar

## Metrics

- precision
- recall
- f1
- false_positive_rate
- evidence_citation_quality
- time_to_first_useful_signal
- reviewer_clarity_rating
- reviewer_actionability_rating
- incremental_lift_over_transcript_only

## Required Gold Labels

- per-case review labels
- evidence spans or windows
- reviewer timing measurements
- reviewer clarity/actionability ratings

## Review Process

1. Run transcript-only review.
2. Run transcript + sidecar review on the same case set.
3. Capture timing, evidence quality, and reviewer ratings.
4. Compare lift only when the same tasks and labels exist for both conditions.

## Success Criteria

- improved reviewer speed without loss of evidence quality
- improved evidence traceability
- lower false positives than a naive sidecar interpretation

## What Counts As Failure

- sidecars create confident claims without transcript support
- false positives rise without reviewer benefit
- reviewers cannot trace the extra signals back to usable evidence
