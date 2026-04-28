# Evaluation Rubric

This rubric is for manual and weak-label review of deterministic transcript signals. It is not a statistical validation claim by itself.

## Label Outcomes

- True positive: a predicted signal matches a gold label on `case_id` and `signal_type`, has compatible direction, and includes evidence text that justifies the signal.
- False positive: a predicted signal has no matching gold label or relies on evidence that does not support the signal.
- False negative: a gold label has no corresponding prediction.
- Bad evidence span: the predicted evidence is empty, too broad, wrong speaker, wrong section, or lacks the phrase needed to justify the signal.
- Bad direction classification: the signal type is plausible but direction is wrong, such as `positive` when the label is `negative` or `mixed`.
- Bad friction classification: the output marks routine analyst questioning as pressure, pushback, or risk without repeated questioning, evasive response, or explicit concern.
- Uncertain or ambiguous label: the evidence supports concern or opportunity but does not clearly establish direction, topic, or management commitment.

## Minimum Evidence Standard

Every non-neutral label needs evidence text. Evidence should be short enough for review but complete enough to show speaker role, topic, and reason. The reviewer should be able to understand why the label exists without reading the entire transcript.

## Vague Guidance Language

Vague language such as "we remain optimistic" or "demand is healthy" is not guidance revision unless it is tied to a prior outlook, current outlook, numeric range, formal guidance language, or explicit management statement about raising, lowering, reaffirming, narrowing, widening, or withdrawing expectations.

## Direction Handling

- `positive`: improvement, raised outlook, stronger commitment, or reduced risk.
- `negative`: lowered outlook, elevated pressure, worsening risk, or unresolved friction.
- `mixed`: credible upside and downside are both present in the same topic.
- `neutral`: no signal or intentionally non-signal example.
- `unknown`: signal exists but direction cannot be assigned safely.

## Reviewer Guidance

When in doubt, prefer `unknown`, `mixed`, or no label over an overstated directional claim. Evidence quality is more important than maximizing signal count.
