# Gold Holdout Set Guide

The current file at `data/nlp_research/gold_holdout_candidates.jsonl` is a candidate locked holdout, not a final gold set.

## Purpose

- preserve a small set of readable, evidence-backed examples for future evaluation
- keep these rows out of training once the set is accepted
- require a second reviewer before any row is promoted to true gold

## Current Status

- candidate count: `16`
- class balance target: `4` rows per class
- current gold status value: `candidate_pending_second_review`
- locked for training: `true`

## Rules

- never train on rows marked `locked_for_training: true`
- do not promote a row to final gold without second-review confirmation
- demote any row that becomes ambiguous during error review
- prefer short, non-PII, evidence-backed rows for future gold promotion

## Promotion Path

1. second reviewer labels the candidate row
2. agreement status is recorded
3. disagreements are resolved or the row is removed
4. only then should the row move from `candidate_pending_second_review` to a stronger gold status
