# Default Branch Transition Plan

## Current Situation

`git remote show origin` reports the GitHub default branch as `main`, while the current best product branch is `signal-engine-2.0`.

That means the public GitHub landing page may show an older README unless GitHub is pointed at the forward branch or the forward branch is merged into `main`.

## Option A: Set `signal-engine-2.0` As Default

Use this when Keith wants the current Signal Engine work to become the repo landing experience immediately without merging into `main`.

Pros:

- Fastest way to show the best README.
- No history rewrite.
- No merge conflict risk.
- Keeps the branch’s evaluation-readiness history intact.

Cons:

- `main` remains behind as a legacy branch.
- Any existing automation expecting `main` may need a quick check.

## Option B: Open PR From `signal-engine-2.0` Into `main`

Use this when Keith wants `main` to remain the default branch and absorb the forward work through GitHub review.

Pros:

- Conventional GitHub workflow.
- Keeps default branch name stable.
- Creates a visible review/merge point.

Cons:

- May surface conflicts because `main` and `signal-engine-2.0` have diverged.
- The public README stays stale until PR merge.

## Recommendation

Choose the path that makes GitHub README show the best work without rewriting history.

For a portfolio-facing repo, Option A is likely the cleanest short-term move: set `signal-engine-2.0` as the default branch. Later, open a PR or create a clean release branch if a consolidated `main` is needed.

## Non-Actions In This Pass

- No merge to `main`.
- No default branch change.
- No force-push.
- No branch deletion.
- No history rewrite.
