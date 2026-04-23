# Portfolio Update Summary

- Repo path: `/Users/keith/GitHub/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026`
- Starting branch: `main` after canonical clone selection and fast-forward to `origin/main`
- Ending branch: `main`
- Changes committed: `yes`
- Pushed: `yes`
- Final commit message: `docs: tighten portfolio positioning and proof path`

## Canonical Clone Decision
- Canonical local clone chosen: `/Users/keith/GitHub/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026`
- Alternate local clone reviewed: `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026`
- Reason: the GitHub clone on `main` already held the cleanest committed, recruiter-safe artifact bundles and was the best public-facing base.

## Key Files Changed
- `README.md`
- `docs/demo-path.md`
- `docs/portfolio-proof.md`
- `docs/current-status.md`
- `Makefile`
- `scripts/build_portfolio_proof.py`
- `scripts/audit_portfolio_docs.py`
- `scripts/refresh_readme_proof.py`
- `scripts/check_proof_freshness.py`
- `outputs/LLY_2025_Q2_call08/portfolio_proof.json`

## What Improved For Recruiter Readability
- One canonical proof path now anchors the repo: `outputs/LLY_2025_Q2_call08/`
- README framing now explains what the system is, why it exists, what goes in, what comes out, and how to run the proof in a few minutes.
- Demo and proof docs now give a short, repeatable walkthrough instead of leaving the reviewer to infer the best path.
- Public wording now emphasizes workflow design and evidence packaging instead of vague AI claims.

## What Improved For Technical Credibility
- Canonical proof checks now generate a machine-readable artifact and refresh the README proof block from committed outputs.
- The repo now links deterministic artifacts, benchmark labels, and bounded multimodal sidecars from one consistent proof case.
- Portfolio copy now states the deterministic-first boundary clearly and explicitly calls out ASR limitations in the chosen benchmark example.
- `make portfolio-ci` now validates the canonical proof path, markdown links, and portfolio helper scripts.

## Preserved But Not Merged Work
- The alternate local clone on `feat/multimodal-sidecars` had meaningful uncommitted docs/app edits.
- Those edits were preserved outside the repo before cleanup as:
  - `/Users/keith/Documents/New project/recovery_backups/earnings_signal_engine_preserve_20260423/noncanonical_portfolio_docs.patch`
  - `/Users/keith/Documents/New project/recovery_backups/earnings_signal_engine_preserve_20260423/noncanonical_portfolio_docs_meta.txt`
- That preserved work was not mass-merged because the public-facing update prioritized a clean, verifiable canonical proof path on `main`.

## Known Limitations Remaining
- The benchmark package is still small and should be presented as prototype evaluation coverage, not broad validation.
- The canonical LLY proof is strongest as an auditable workflow walkthrough; guidance revision matching remains partial in the committed bundle.
- Multimodal coverage remains supportive and limited in breadth.
