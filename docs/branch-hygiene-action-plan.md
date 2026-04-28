# Branch Hygiene Action Plan

## Current Branch State

- Current branch: `signal-engine-2.0`
- Remote: `git@github.com:keithtgrehan/earnings-call-signal-engine.git`
- GitHub default branch from `git remote show origin`: `main`
- Local branch count observed: 27
- Remote branch count observed: 8

## Local Branches Observed

- `backup/2026-04-23`
- `chore/canonical-repo-hardening-and-salvage`
- `chore/reference-case-standardization`
- `codex/clean-multimodal-merge`
- `codex/hardening-batch-runbook`
- `codex/netflix-demo-case`
- `feat/batch-handoff-blackwell`
- `feat/chunking-embedding-support-layer`
- `feat/demo-case-nvidia-q4-fy2024`
- `feat/fix-demo-mode-ui`
- `feat/meta-q3-2022-reference-case`
- `feat/model-sidecars-benchmark`
- `feat/model-sidecars-runtime-cleanup`
- `feat/model-sidecars-runtime-hardening`
- `feat/multimodal-sidecars`
- `feat/netflix-multimodal-evidence-panel`
- `feat/netflix-multimodal-polish`
- `feat/netflix-reference-case-hardening`
- `feat/nlp-sidecar-eval-pack`
- `feat/presentation-hardening-thursday`
- `feat/support-qa-risk-engine-v1`
- `integration/model-sidecars-runtime-cleanup`
- `main`
- `preserve/noncanonical-portfolio-docs-20260423`
- `safety/support-qa-recovery-20260424-120624`
- `safety/sync-20260424-130930`
- `signal-engine-2.0`

## Remote Branches Observed

- `origin/main`
- `origin/signal-engine-2.0`
- `origin/chore/reference-case-standardization`
- `origin/codex/audio-youtube-fix`
- `origin/codex/feat/guidance-revision`
- `origin/codex/overnight/guidance-benchmark-batch`
- `origin/feat/pilot-corpus-and-multimodal-intake`

## Recommendation

Recommended presentation path: make `signal-engine-2.0` the default branch, or open a PR from `signal-engine-2.0` into `main`.

Choose the path that makes the GitHub landing README show the current Signal Engine work without rewriting history.

## Stale Branch Candidates

Likely safe to delete after confirmation:

- old local `codex/*` branches with no current remote tracking branch
- old local `feat/*` branches superseded by `signal-engine-2.0`
- old `safety/*` or `preserve/*` branches after confirming all useful work is merged or documented

Keep:

- `signal-engine-2.0`
- `main`
- any branch currently used by another Codex/session
- `preserve/*` or `safety/*` branches until Keith confirms they are no longer needed

Unknown/risky:

- branches with worktree markers shown by `git branch` as `+`
- branches with remote tracking status not yet reviewed
- branches tied to legacy demo/proof assets

## GitHub UI Steps To Change Default Branch

1. Open the GitHub repo.
2. Go to `Settings`.
3. Go to `Branches`.
4. Under `Default branch`, choose the switch/edit control.
5. Select `signal-engine-2.0`.
6. Confirm the default branch change.
7. Re-check the repo landing page README.

## Safe Branch Deletion Commands

Do not run these until each branch is confirmed obsolete.

```bash
git branch --merged signal-engine-2.0
git branch -d <local-branch-name>
git push origin --delete <remote-branch-name>
```

For unmerged branches, do not use `-D` unless Keith explicitly approves after reviewing the branch contents.
