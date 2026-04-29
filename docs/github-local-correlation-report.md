# GitHub Local Correlation Report

## Summary

Local `signal-engine-2.0` and remote `origin/signal-engine-2.0` match at the current Signal Engine README commit. The configured remote uses SSH rather than the exact HTTPS URL, but it points to the same GitHub repository.

## Repo And Remote

- Local repo path: `/Users/keith/Documents/New project/earnings-call-signal-engine-support-qa`
- Current local branch: `signal-engine-2.0`
- Configured origin URL: `git@github.com:keithtgrehan/earnings-call-signal-engine.git`
- Expected HTTPS URL: `https://github.com/keithtgrehan/earnings-call-signal-engine.git`
- Exact URL match: `false`
- Same GitHub repo via SSH transport: `true`

## Branch Heads

- Local `signal-engine-2.0` HEAD: `9c68dc114df10da38ff9938626bbfadb39f37ddb`
- `origin/signal-engine-2.0` HEAD after explicit fetch: `9c68dc114df10da38ff9938626bbfadb39f37ddb`
- `origin/main` HEAD: `e46562c55157b957652091883c32ca23e92ae5ad`
- Local and remote `signal-engine-2.0` match: `true`

Note: a plain `git fetch origin` did not update the local `origin/signal-engine-2.0` tracking ref in this checkout, but `git ls-remote origin signal-engine-2.0` showed the remote branch at `9c68dc1`. An explicit fetch of `signal-engine-2.0:refs/remotes/origin/signal-engine-2.0` brought the local tracking ref into alignment.

## README Comparison

- Local `signal-engine-2.0:README.md`: current `# Signal Engine` positioning.
- `origin/signal-engine-2.0:README.md`: current `# Signal Engine` positioning after explicit tracking-ref refresh.
- `origin/main:README.md`: older `# Earnings Call Signal Engine` positioning.
- README differs between `signal-engine-2.0` and `main`: `true`

If the public GitHub repo still shows the old README, the most likely causes are:

- viewing `main` explicitly, such as a `/tree/main` URL,
- browser/GitHub rendering cache,
- stale local remote-tracking state before the explicit fetch,
- or looking at a fork/alternate remote.

It is not a wrong remote problem: the configured SSH origin points to `keithtgrehan/earnings-call-signal-engine`.

## GitHub Default Branch

`git remote show origin` reports:

- HEAD branch: `signal-engine-2.0`

That means the public root repo page should show the `signal-engine-2.0` README, not `main`, once GitHub rendering catches up and the viewer is not pinned to another branch.

## Main Branch Status

`origin/main` is stale relative to `signal-engine-2.0`.

Do not merge automatically. Safe options:

- Option A: keep `signal-engine-2.0` as the default branch.
- Option B: open a PR from `signal-engine-2.0` into `main`.

Recommended next action: keep `signal-engine-2.0` as default for the portfolio-facing view, then decide later whether to PR into `main`.

## Heavy / Generated Presentation Risks

Tracked heavy/generated-looking paths were reviewed but not deleted.

Intentional portfolio proof:

- `outputs/LLY_2025_Q2_call08/portfolio_proof.json`
- selected checked-in proof/demo outputs used by earlier portfolio workflows

Legacy artifacts:

- `outputs_prior/*`
- `outputs/GOOGL_2025_Q4_call03/*`
- `outputs/IBM_2025_Q4_call04/*`
- `outputs/MSFT_2026_Q2_call05/*`
- `outputs/PLTR_2025_Q4_call01/*`
- processed demo/corpus outputs under `data/corpus/processed/` and `data/processed/`

Cleanup candidates after manual review:

- `models/media_support/*.joblib`
- old `outputs_prior/*`
- old multimodal/text-emotion generated outputs
- demo-case PDFs and generated reports that are not needed for the current Signal Engine 2.0 landing path

No cleanup was performed because these files may preserve meaningful project history or proof artifacts.

## Commands Run

```bash
pwd
git rev-parse --show-toplevel
git remote -v
git branch --show-current
git status --short
git log --oneline -10
git ls-remote --heads origin
git ls-remote origin signal-engine-2.0
git ls-remote origin main
git remote show origin
git fetch origin
git rev-parse signal-engine-2.0
git rev-parse origin/signal-engine-2.0
git rev-parse origin/main
git log origin/signal-engine-2.0 --oneline -5
git show signal-engine-2.0:README.md | head -80
git show origin/signal-engine-2.0:README.md | head -80
git show origin/main:README.md | head -80
git ls-files | grep -E '^(outputs|outputs_prior|models|slides)/' | sort
find outputs outputs_prior models slides -type f -maxdepth 3 2>/dev/null | head -100
git fetch origin signal-engine-2.0:refs/remotes/origin/signal-engine-2.0
```

## Exact Recommended Next Action

Open the public repository root at `https://github.com/keithtgrehan/earnings-call-signal-engine` and confirm the branch selector shows `signal-engine-2.0`. If it does, the README should be the current `# Signal Engine` README. If GitHub still displays the old README at the root URL, refresh/clear cache or verify the URL is not pinned to `/tree/main`.
