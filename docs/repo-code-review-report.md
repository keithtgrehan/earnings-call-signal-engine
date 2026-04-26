# Repo Code Review Report

## P0

- `README.md` contained banned `alpha` wording, which caused `python scripts/audit_portfolio_docs.py` to fail and directly undermined the portfolio-doc validation path.

## P1

- `docs/signal-error-analysis.md` embedded absolute local filesystem paths, which hurts portability and makes the artifact look machine-local rather than repo-ready.
- `docs/demo-path.md` and `docs/portfolio-proof.md` linked directly to optional legacy proof files that are not present in a clean checkout, which created noisy markdown-link warnings in the default doc audit flow.

## P2

- `README.md` already had multiple status and roadmap sections, but it did not have one concise “Current State vs Roadmap” block that clearly separates what works now from optional or blocked paths.
- The repo still has a broad dual-lineage surface: `src/signal_engine/` is the current canonical path while legacy and sidecar assets remain visible in `src/earnings_call_sentiment/`, `src/parser.py`, and the larger `scripts/` directory. This is not a blocker, but it increases orientation cost.
- `.github/` is not present in the local checkout, so GitHub Actions workflow review could not be performed from local files in this pass.
