# Portfolio Product V1 Evaluation Contract

Status: accepted methodology; evaluation data is not yet publication-ready.

## Purpose

Compare bounded reviewer models on the same task while preserving the existing
deterministic extractor as the canonical baseline.

The current repository contains early and mixed-provenance labels. Its strict
provenance-complete gold count must be repaired and revalidated before public
model-quality claims. No legacy headline metric is silently carried into this
case study.

## Unit of Evaluation

One immutable evidence bundle contains:

- case and source identifiers;
- source URL/path, rights status, acquisition date, and content hash;
- transcript section and speaker metadata;
- deterministic signal candidate and exact evidence span;
- task schema version;
- human-review status and audit metadata.

Raw rights-restricted transcript bodies remain outside Git.

## Dataset Plan

- Build 80 to 120 human-reviewed evidence bundles from approximately 25 to 40
  rights-cleared calls or filing exhibits.
- Run a calibration batch before scaling review.
- Separate development and locked holdout data before final model selection.
- Target at least 25 percent for the untouched holdout.
- Record reviewer, timestamp, decision, confidence, notes, provenance, and hash.
- External datasets may test robustness but cannot replace project-specific gold
  labels or enter the headline score without separate reporting.

## Reviewer Models

Start with two Bedrock-hosted models from different providers using identical
evidence, instructions, schema, timeout, and retry policy. A third higher-cost
model is allowed only if the first two do not establish a defensible trade-off.

Models may critique, classify, explain, or abstain. They may not alter the
canonical evidence bundle or promote labels.

## Successful Analysis

A run is successful only when all are true:

- response validates against the versioned schema;
- human review finds the signal decision correct for the task;
- cited evidence supports the decision;
- insufficient evidence leads to an appropriate abstention;
- the run completes within the documented timeout;
- no privacy, permission, or data-rights boundary is violated.

## Metrics

- Human-judged correctness.
- Evidence-support/faithfulness rate.
- Precision, recall, and F1 where the label design supports them.
- Abstention quality and false-positive/false-negative analysis.
- Schema compliance and failure/retry rate.
- p50 and p95 latency.
- Input/output tokens and model cost per attempt.
- Total model and estimated infrastructure cost per successful analysis.
- Human review time and edit/rejection rate.

## Reporting Rules

- Freeze prompts, schema, model IDs, region, parameters, code SHA, and dataset
  version for the final comparison.
- Do not tune on the holdout set.
- Report denominators and confidence intervals where appropriate.
- Show failure cases and disagreement, not only aggregate scores.
- Label all results small-sample, human-reviewed, and non-production.
- Do not imply trading performance, causality, alpha, or professional replacement.
