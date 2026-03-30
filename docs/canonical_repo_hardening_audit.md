# Canonical Repo Hardening Audit

## Repo Paths

- Canonical repo path: `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026`
- Active hardening worktree path: `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-hardening`
- Legacy reference repo path: `/Users/keith/GitHub/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026`

## Branch For This Work

- Requested branch: `chore/canonical-repo-hardening-and-salvage`
- Base used: clean local `main` at `7296bd8` after confirming it matched `origin/main`

## Current Remote Info

- `origin` fetch: `git@github.com:keithtgrehan/earnings-call-signal-engine.git`
- `origin` push: `git@github.com:keithtgrehan/earnings-call-signal-engine.git`

## Initial State Notes

- The canonical repo's primary checkout was already on `feat/multimodal-sidecars` with unrelated local modifications and untracked media artifacts.
- To avoid disturbing that in-progress work, this hardening pass was started from a fresh linked worktree created from clean `main`.
- Local `main` and `origin/main` matched before work began.

## What This Hardening Pass Aims To Do

- Audit the legacy clone strictly as reference material and selectively salvage only low-risk ideas.
- Reduce confusion between canonical and legacy local repos.
- Tighten media-support evaluation and readiness wording where it materially improves reviewer clarity.
- Fix small in-scope bugs, docs drift, path footguns, and weak tests encountered in touched areas.
- Preserve deterministic transcript-first behavior as the canonical path.
- Leave a clean reviewer trail on a non-main branch only.

## What This Hardening Pass Will Not Do

- It will not develop in the legacy clone.
- It will not push or commit to `main`.
- It will not weaken or replace the deterministic transcript-first path.
- It will not add predictive-edge or statistical-significance claims.
- It will not broaden scope into new case studies, UI redesign, or speculative framework expansion.
