# Branch Uniqueness Audit

## Commands

- `git log --oneline origin/main..origin/signal-engine-2.0`
- `git log --oneline origin/main..origin/codex/ilya-paper-full-asset-ingestion`
- `git log --oneline origin/main..origin/codex/nlp-assets-tooling-registry`

## Findings

### `origin/signal-engine-2.0`

Contains the original Signal Engine 2.0 proof history, including pilot corpus intake, deterministic support QA, conversation intelligence, emotion benchmark scaffolding, multimodal foundation, data-growth workflow, evaluation backbone, and the merged Ilya reading-list PR.

Recommendation: `keep` until the rebased proof branch lands in `main`; then `archive` after confirming no unique source/manifests/docs remain.

### `origin/codex/ilya-paper-full-asset-ingestion`

Contains the Ilya reading-list research layer, full paper asset ingestion, and NLP asset registry work on top of the older branch line. These assets are represented in the rebased proof branch history.

Recommendation: `archive` after the consolidated proof branch is merged into `main`. Do not delete before verifying the full research docs, source registry, extracted metadata, NLP asset registry, and CLIs exist on `main`.

### `origin/codex/nlp-assets-tooling-registry`

Before push, the remote branch still points to the older, pre-rebase branch line. The local branch has been rebased onto `origin/main` and is the clean consolidation candidate.

Recommendation: `merge` the rebased local branch into `main` through PR review, then archive or delete the remote feature branch after merge.

## Duplicate Or Obsolete Branches

- `signal-engine-2.0`: useful historical/default branch, but should stop being the public default after `main` contains the proof state.
- `codex/ilya-paper-full-asset-ingestion`: likely duplicate after the consolidated proof branch lands.
- `codex/ilya-research-paper-intelligence-layer`: superseded by full paper asset ingestion and the consolidated proof branch.

## Preservation Bias

Keep source logic, manifests, docs, tests, registry files, and representative proof samples. Bulky generated artifacts may be regenerated or ignored, but source logic and proof manifests should not disappear during branch cleanup.
