# Human Review Guidelines

Human review converts deterministic suggestions into trusted labels. Reviewers should treat weak labels as prompts for inspection, not answers.

## Reviewer Responsibilities

- Read the chunk text and nearby context when needed.
- Accept only labels supported by the evidence.
- Remove labels that are weak, generic, or unsupported.
- Add missing labels only when the chunk clearly supports them.
- Leave ambiguous cases unresolved or rejected rather than forcing a label.
- Preserve reviewer identity and review timestamp in exported rows.

## Signal Guidance

- `guidance_revision`: explicit change or reaffirmation of guidance, outlook, target, forecast, or expectation.
- `tone_shift`: meaningful change in management tone, emphasis, or stance.
- `analyst_pressure`: analyst challenge, pushback, repeated probing, or pressure around a business issue.
- `uncertainty`: material uncertainty, risk, volatility, or lack of visibility.
- `evasive_answer`: answer avoids or deflects a specific question.
- `positive_surprise`: positive result, upside, acceleration, or materially better-than-expected signal.
- `negative_surprise`: miss, deceleration, pressure, downside, or materially worse-than-expected signal.

## Export Boundary

Only explicitly reviewed or approved records may be exported. Rejected suggestions, corrected labels, and removed labels should remain available for error analysis and future disagreement sampling.

## What Not To Do

- Do not auto-accept suggestions.
- Do not infer labels from weak-label confidence alone.
- Do not treat Argilla as the only system of record.
- Do not mutate raw transcript files during review.
- Do not claim benchmark validity from small reviewed samples.
