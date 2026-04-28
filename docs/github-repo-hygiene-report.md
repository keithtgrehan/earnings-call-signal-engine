# GitHub Repo Hygiene Report

## Current State

- Current branch: `signal-engine-2.0`
- Local branch count: 27
- Remote branch count: 8
- Tags: 2
- Tracked file count: 822
- GitHub remote: `git@github.com:keithtgrehan/earnings-call-signal-engine.git`
- Remote default branch: `main`

No destructive actions were taken. No branches were deleted, no history was rewritten, and no force-push was used.

## Branch Review

The branch list contains many legacy local branches plus a smaller set of remote branches. Several local branches appear to be historical feature, safety, or preservation branches.

Stale branch candidates for later manual review include old `feat/*`, `codex/*`, `safety/*`, and `preserve/*` branches that are already merged, obsolete, or superseded. This report does not recommend deleting any branch automatically.

## Default Branch Recommendation

Recommended stance: do not merge or switch defaults automatically from this task.

`signal-engine-2.0` is the strongest forward product branch for the current deterministic transcript-first evaluation story. Once Keith is ready to make it the public landing experience, the safest next step is either:

- open a PR from `signal-engine-2.0` into `main`, or
- make `signal-engine-2.0` the GitHub default branch after confirming the branch is the desired public presentation.

Avoid squashing or rewriting existing history unless creating a separate clean release branch later.

## README Presentation Risk

The branch README is aligned with the current scope: deterministic transcript-first system, scaffolded registries, no validated ML claims, and no corpus/retrieval overclaims.

GitHub currently points `origin/HEAD` at `origin/main`, so the public default-branch README may still be stale relative to `signal-engine-2.0`.

## Large Tracked File Findings

Largest tracked files are legacy processed/demo artifacts, not new files from this pass. Examples include:

- `data/corpus/processed/evidence_objects/LLY_2025_Q2_call08.evidence_objects.jsonl`
- `data/processed/multimodal/nlp/msft_fy26_q2_example/nlp_segment_scores.json`
- `data/corpus/processed/chunks/LLY_2025_Q2_call08.event_chunks.jsonl`
- `data/demo_cases/netflix_q1_2022/raw/transcript/netflix_q1_2022_transcript.pdf`
- `data/demo_cases/meta_q3_2022/raw/presentation/meta_q3_2022_earnings_presentation.pdf`

These were not removed because they may be meaningful historical proof assets.

## Generated / Heavy Artifact Findings

Tracked generated or heavy-adjacent assets already exist in legacy areas:

- processed corpus chunks and evidence objects
- demo case PDFs
- processed multimodal/NLP outputs
- legacy image/chart outputs
- small model artifacts under existing model paths

No new transcript, dataset, model weight, audio, video, or API output was added by this task.

## Safe Cleanup Plan

1. Keep `signal-engine-2.0` as the forward working branch.
2. Decide whether to open a PR into `main` or change the GitHub default branch to `signal-engine-2.0`.
3. Inventory stale branches in a separate review pass.
4. Delete stale branches only after confirming they are merged or obsolete.
5. Leave meaningful historical proof artifacts in place unless Keith explicitly approves a cleanup branch.
6. Keep raw manually acquired corpus transcripts ignored and out of commits.

## Explicit Non-Actions

- No branch deletion.
- No merge to `main`.
- No default branch change.
- No transcript download.
- No raw transcript commit.
- No model/dataset/audio/video/API artifact commit.
- No source extraction behavior changes.
