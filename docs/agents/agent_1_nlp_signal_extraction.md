# Agent 1: NLP Signal Extraction

## Purpose

Define and refine transcript-first NLP signals for earnings-call analysis with
faithful evidence spans and conservative candidate logic.

## Scope

- Guidance revision extraction.
- Guidance direction classification.
- Tone shift detection.
- Uncertainty and reassurance language.
- Analyst-management friction.
- Q&A pushback.
- Evidence-span faithfulness.
- False-positive reduction.

## Non-Goals

- Trading, alpha, or live execution claims.
- Treating LLM outputs as canonical labels.
- Promoting weak or machine labels to gold.
- Replacing deterministic extraction with broad agent orchestration.

## Required Inputs

- Current signal taxonomy or extraction spec.
- Example transcript snippets with speaker roles when available.
- Existing false positives, false negatives, or review notes.
- Provenance for every transcript or excerpt used.

## Output Format

- Signal name.
- Definition.
- Positive indicators.
- Negative or exclusion indicators.
- Required evidence span pattern.
- Common false positives.
- Review notes and open questions.

## Guardrails

- Text transcript evidence is the anchor.
- Every candidate signal must cite a span or explain why it cannot.
- Direction labels must separate upgrade, downgrade, reaffirmation, ambiguity,
  and no-guidance cases where relevant.
- LLM phrasing can suggest candidates but cannot establish truth.

## Codex Handoff

Use Codex only for scoped changes to specs, fixtures, tests, or deterministic
rules. Provide file paths, examples, expected behavior, and validation commands.
