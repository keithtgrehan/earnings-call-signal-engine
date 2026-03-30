# Repo Hygiene Map

## Canonical And Legacy Paths

- Canonical repo: `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026`
- Legacy reference clone: `/Users/keith/GitHub/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026`

## Discoverable Worktrees

- `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026`
  - branch: `feat/multimodal-sidecars`
  - state: dirty
  - guidance: do not use as a clean starting point
- `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-reference-standardization`
  - branch: `chore/reference-case-standardization`
  - state: clean worktree for Part A of this task
- `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-hardening`
  - branch: `chore/canonical-repo-hardening-and-salvage`
  - state: prior canonical hardening branch
- `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-model-sidecars`
  - branch: `feat/model-sidecars-benchmark`
  - state: separate feature worktree
- `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-runtime-hardening`
  - branch: `feat/model-sidecars-runtime-hardening`
  - state: separate feature worktree
- `/Users/keith/Documents/New project/main-demo-wt`
  - branch: `feat/netflix-reference-case-hardening`
  - state: frozen Netflix reference-case worktree; use read-only for comparison or validation
- `/Users/keith/Documents/New project/ecs-clean-merge`
  - branch: `codex/hardening-batch-runbook`
  - state: unrelated worktree for another task

## Safe Branch Guidance

- Safe starting branch for new bounded work:
  - `main`, but only from a clean worktree
- Safe review branches created in this task family:
  - `chore/canonical-repo-hardening-and-salvage`
  - `chore/reference-case-standardization`

## Frozen / Reference-Only Branch Guidance

- `feat/netflix-multimodal-evidence-panel`
  - use as the initial Netflix bounded-pack reference
- `feat/netflix-multimodal-polish`
  - use as the intermediate Netflix polish reference
- `feat/netflix-reference-case-hardening`
  - use as the current Netflix gold reference for reviewer-safe packaging and interpretation rules

These branches should be read as reference material, not as new general-purpose framework branches.

## What Should Be Ported Later

- small reusable validator/helpers
- supporting-only wording standards
- honest missing-bundle / skip behavior
- asset-audit / handoff / PR-note document patterns

## What Should Be Ignored

- active dirty state in the primary canonical checkout
- the dirty legacy clone as a development target
- unrelated experimental worktrees unless the task explicitly calls for them

## Practical Operator Guidance

- Do not start new bounded work from the dirty primary canonical checkout.
- Create a fresh worktree from clean `main` for each bounded review branch.
- Treat the legacy clone as historical/reference-only unless a task explicitly requires read-only comparison.
- When auditing a reference case, prefer branch/worktree inspection over copying code blindly.
- If a requested media path differs from the actual file used, record that distinction explicitly in the asset audit.
