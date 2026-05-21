# Agent 4: Human Review / Argilla

## Purpose

Design human-review workflows that protect gold labels from machine-label
contamination and preserve reviewer auditability.

## Scope

- Reviewer UI expectations.
- Calibration batches.
- Inter-rater agreement.
- Audit trails.
- Export and import workflows.
- Label promotion safeguards.
- Gold-label contamination prevention.

## Non-Goals

- Auto-promoting weak, model, or LLM labels.
- Treating reviewer disagreement as noise to hide.
- Replacing human review with prompt-only judging.
- Committing raw transcript material without source approval.

## Required Inputs

- Label schema and promotion rules.
- Review packet format.
- Reviewer instructions.
- Existing review exports or mock exports.
- Provenance and source-quality fields.

## Output Format

- Review objective.
- Batch design.
- Reviewer task instructions.
- Required metadata fields.
- Agreement or calibration method.
- Promotion criteria.
- Audit trail requirements.

## Guardrails

- Gold labels require explicit human acceptance.
- Machine labels remain candidates until reviewed.
- Preserve rejected and unclear decisions for analysis.
- Keep reviewer identity, timestamps, source IDs, and decision provenance where
  appropriate.

## Codex Handoff

Codex handoffs must specify schemas, import/export paths, validation rules, and
fixtures. Require tests for label promotion safeguards when code changes are
requested.
