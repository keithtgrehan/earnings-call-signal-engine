# Reviewer Guidelines

Reviewers decide whether deterministic transcript signal candidates are good enough to become canonical gold labels.

## Responsibilities

- Judge the visible evidence, not the system's confidence score.
- Preserve the evidence span when it is correct.
- Use `edit` or `relabel` only when the row can be corrected without guessing.
- Use `uncertain` when context is insufficient.
- Use `reject` for boilerplate, vague sentiment, keyword-only hits, or unsupported claims.

## Boundaries

Deterministic extraction creates candidates. Reviewers create truth. Argilla is only a review interface. Gold labels are only produced by the guarded import path.

Do not add private reviewer notes to committed files. Reviewer notes should explain label reasoning, evidence limitations, or ambiguity in a way that can be audited later.

## Lifecycle

- `pending`: candidate created but not assigned or reviewed.
- `in_review`: reviewer is actively working the row.
- `accepted`: candidate is correct as shown.
- `rejected`: candidate should not become gold.
- `edited`: candidate is usable after bounded correction.
- `relabeled`: evidence is useful but label changes.
- `uncertain`: evidence is insufficient.
- `adjudication_required`: reviewers disagree or the row needs a final decision.

## Evidence Checklist

- Is the evidence text exact and source-backed?
- Does the evidence support the signal type?
- Is the transcript section correct?
- Is the speaker role correct?
- Is the direction explicit enough?
- Would another reviewer understand the decision from this row alone?

If the answer is no, reject, edit, relabel, or mark uncertain.
