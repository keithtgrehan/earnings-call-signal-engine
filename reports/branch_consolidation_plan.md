# Branch Consolidation Plan

## Current Branch State

- GitHub default branch: `signal-engine-2.0`
- Local proof branch: `codex/nlp-assets-tooling-registry`
- Intended clean target: `main`
- `origin/HEAD` points to `origin/main`

## Main Versus Proof Branch

`main` does not yet contain the consolidated proof state. The rebased `codex/nlp-assets-tooling-registry` branch carries the evaluation loop, 57-label proof state, NLP asset registry, Ilya research assets, pilot corpus/retrieval scaffolding, dataset adapters, embedding benchmark harness, and portfolio README cleanup.

## signal-engine-2.0

`origin/signal-engine-2.0` contains useful historical work and is currently the GitHub default branch. Most of its useful source/docs/manifests are represented in the rebased proof branch, but commit hashes differ because the proof branch was replayed onto `origin/main`.

Recommendation: keep `signal-engine-2.0` until the proof branch is merged into `main` and full validation is green. After that, archive it as historical or delete it only after confirming there are no unique files missing from `main`.

## Recommended Merge Order

1. Push `codex/nlp-assets-tooling-registry` with `--force-with-lease`.
2. Open or retarget a PR from `codex/nlp-assets-tooling-registry` to `main`.
3. Confirm CI and local validation.
4. Merge into `main`.
5. Change GitHub default branch to `main` only after `main` contains the proof state and tests pass.
6. Then review whether `signal-engine-2.0` can be archived.

## Explicit Warning

Do not change the GitHub default branch until `main` contains the consolidated proof state and validation has passed on the merge candidate.
