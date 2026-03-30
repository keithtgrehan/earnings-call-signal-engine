# Netflix Multimodal Polish Audit

## Scope

- Branch goal: strengthen the fixed `netflix_q1_2022` multimodal pack without changing the transcript-first deterministic core.
- This audit is limited to the existing Netflix multimodal artifacts, supporting renderer code, and nearby tests.
- No recommendation here broadens scope to other companies, new claims, or a new multimodal framework.

## What Is Already Strong

- The pack repeatedly states the correct boundary: deterministic transcript-backed outputs are canonical and sidecars/audio/video are supporting-only.
- The asset audit now clearly distinguishes the exact requested MP4 path from the fallback local MP4 that was actually used.
- The moment set is already bounded to 11 curated rows with a fixed top-8 subset, which keeps the demo reviewable.
- The output surface is persistent and reviewer-friendly in shape: manifest, comparison, disagreement panel, pressure panel, clip manifest, and markdown summaries are all committed.
- The code already rejects stronger claims in several places: no predictive lift, no statistical significance, no emotion/deception framing, and no overwrite of deterministic artifacts.

## What Is Noisy

- Reviewer notes are too repetitive. Many different moments currently collapse to the same generic “sidecars split” wording, which makes the pack harder to scan.
- Several `why_selected` fields still read a little presentation-first rather than reviewer-first.
- Disagreement ranking mostly follows existing moment rank instead of distinguishing genuinely meaningful directional conflict from label-space mismatch or non-polar moments.
- Audio interpretation text is mostly careful, but some phrasing still leans closer to interpretation than the underlying measured cues warrant.
- Visual outputs still use `supportive` language in several fields even though the current visual layer is heuristic fallback only.

## What Is Misleading Or At Risk Of Reviewer Pushback

- The heuristic visual layer can still read stronger than intended because `support_direction: supportive` and similar phrases sound closer to corroboration than bounded context.
- `strong_supporting_alignment_moments` and some summary wording can be read as stronger endorsement than the conservative reviewer boundary really supports.
- Non-polar moments like the ad-supported answer and financial anchor currently sit near true disagreement rows, which can make ordinary label-space mismatch look more meaningful than it is.
- Some deterministic summaries and `why_selected` text are longer or more rhetorical than necessary, which adds friction in review.
- The pack is already bounded to Netflix, but the branch still contains reusable sidecar plumbing; reviewers may need explicit help separating branch plumbing from product/demo claims.

## What Can Be Improved Safely

- Make reviewer notes more moment-specific without changing the underlying evidence.
- Tighten `why_selected` wording so it explains review value directly and avoids hype.
- Improve disagreement classification and ranking so “directional conflict,” “non-polar context,” and “label-space mismatch” are easier to separate.
- Weaken visual wording wherever heuristic fallback adds only limited observational context.
- Clarify audio wording so it sticks to measured cues, transcript alignment limits, and reviewer utility.
- Improve README / summary ordering so reviewers know which files to open first and why.
- Add focused tests for supporting-only wording, showcase integrity, disagreement output shape, and visual fallback expectations.

## What Should Not Be Touched

- The deterministic transcript-first pipeline and canonical deterministic outputs.
- The bounded Netflix-only scope of the multimodal claim.
- The no-predictive / no-statistical / no-psychological-inference boundary.
- The requirement that audio and video remain supporting-only and optional.
- The fixed-case demo framing; this should not turn into a broad multi-company multimodal rollout.
- Moment-count expansion for novelty’s sake. The existing 11-moment pack is sufficient unless a replacement is clearly stronger than a current weak row.

## Recommended Polish Priorities

- First: reduce reviewer friction by improving notes, wording, and disagreement prioritization.
- Second: weaken heuristic visual language so it cannot be misread as corroboration.
- Third: tighten tests around the exact bounded behaviors this pack is supposed to preserve.
