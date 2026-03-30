# Repo Hygiene Map

## Canonical And Legacy Paths

- Canonical repo: `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026`
- Legacy reference clone: `/Users/keith/GitHub/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026`

## Operator Check First

- Run `git worktree list` before starting any bounded review or fix pass.
- Reuse an existing clean worktree for the target branch when one already exists.
- Treat the worktree inventory below as a current map, not a forever-stable list.

## Discoverable Worktrees

- `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026`
  - branch: `feat/multimodal-sidecars`
  - state: dirty
  - guidance: do not use as a clean starting point
- `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-reference-standardization`
  - branch: `chore/reference-case-standardization`
  - state: clean
  - guidance: use for reference-case standard / parity / repo-hygiene review work
- `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-meta-reference-case`
  - branch: `feat/meta-q3-2022-reference-case`
  - state: clean
  - guidance: use for Meta reference-case review and bounded fixes
- `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-chunking-embedding`
  - branch: `feat/chunking-embedding-support-layer`
  - state: clean
  - guidance: use for retrieval-layer review and bounded fixes
- `/Users/keith/Documents/New project/main-demo-wt`
  - branch: `feat/netflix-reference-case-hardening`
  - state: clean
  - guidance: use for Netflix reference-case inspection and bounded reviewer-safety fixes when needed
- `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-hardening`
  - branch: `chore/canonical-repo-hardening-and-salvage`
  - state: clean
  - guidance: prior canonical hardening branch; not part of the active review lanes
- `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-model-sidecars`
  - branch: `feat/model-sidecars-benchmark`
  - state: clean
  - guidance: separate feature worktree
- `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-runtime-hardening`
  - branch: `feat/model-sidecars-runtime-hardening`
  - state: clean
  - guidance: separate feature worktree
- `/Users/keith/Documents/New project/ecs-clean-merge`
  - branch: `codex/hardening-batch-runbook`
  - state: unrelated worktree for another task

## Safe Branch Guidance

- Safe branch/worktree pairings for current bounded verification work:
  - `chore/reference-case-standardization` in `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-reference-standardization`
  - `feat/meta-q3-2022-reference-case` in `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-meta-reference-case`
  - `feat/chunking-embedding-support-layer` in `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-chunking-embedding`
  - `feat/netflix-reference-case-hardening` in `/Users/keith/Documents/New project/main-demo-wt`
- If a requested branch does not already have a clean worktree, create a sibling worktree rather than reusing a dirty checkout.
- Do not start bounded verification work from `main` unless you intentionally created a clean dedicated worktree for it.

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
- Run `git worktree list` and pick the clean branch-specific worktree before you create anything new.
- Create a fresh worktree from clean `main` only when the needed branch does not already have a clean worktree.
- Treat the legacy clone as historical/reference-only unless a task explicitly requires read-only comparison.
- When auditing a reference case, prefer branch/worktree inspection over copying code blindly.
- If a requested media path differs from the actual file used, record that distinction explicitly in the asset audit.
