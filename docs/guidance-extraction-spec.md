# Guidance Extraction Spec

Guidance extraction is a deterministic transcript-review target, not a production ML claim. The first benchmark should focus on whether rule outputs can find explicit guidance language with defensible evidence spans.

## Required Concepts

- Prior guidance: the earlier outlook, range, target, or management expectation being compared against.
- Current guidance: the current-call outlook, range, target, reaffirmation, withdrawal, or qualifying update.
- Topic: the business measure being discussed, such as revenue, margin, EPS, capex, cash flow, segment growth, demand, or cost.
- Evidence span: the smallest transcript text that supports the signal and direction.

## Direction Classification

- Raised: current guidance is higher or more favorable than prior guidance.
- Lowered: current guidance is lower or less favorable than prior guidance.
- Reaffirmed: current guidance explicitly confirms prior guidance.
- Withdrawn: management explicitly removes or suspends guidance.
- Narrowed: range tightens without necessarily raising or lowering midpoint.
- Widened: range expands or uncertainty increases.
- Unclear: guidance-related language exists but direction cannot be safely inferred.

## Extraction Steps

1. Detect explicit guidance cues such as "guidance", "outlook", "expect", "forecast", "range", "raise", "lower", "reaffirm", "withdraw", "narrow", or "widen".
2. Identify whether the speaker is management and whether the transcript section is prepared remarks or Q&A.
3. Attach the guidance cue to a topic.
4. Compare current language against prior language only when both are present or the current language explicitly references a prior outlook.
5. Emit evidence with case ID, section, speaker, and span metadata.
6. Leave direction as `unknown` when the text is guidance-adjacent but not directionally safe.

## Generic Optimism Exclusion

Generic optimism is not guidance. Phrases like "we are excited", "momentum is strong", or "we see opportunity" should not trigger guidance revision unless they are tied to formal outlook language, a measurable target, or an explicit change in expectations.
