# Reference Case Standardization Audit

## Scope

- Canonical repo audited: `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026`
- Reference branches inspected:
  - `feat/netflix-multimodal-evidence-panel`
  - `feat/netflix-multimodal-polish`
  - `feat/netflix-reference-case-hardening`
  - `main`

## What Already Exists

- `main` already has a strong transcript-first baseline:
  - deterministic review artifacts are canonical
  - audio and visual layers are optional and quality-gated
  - demo cases for Netflix, Meta, and NVIDIA already exist in transcript-first form
  - media-support evaluation scaffolding already exists under `data/media_support_eval/`
- The Netflix reference branches already show a fuller bounded multimodal pack:
  - persistent multimodal panel JSON/markdown
  - curated moment manifest
  - disagreement and pressure subpanels
  - supporting-only caveats bundle
  - explicit asset audit / panel summary / PR handoff docs
  - explicit heuristics-vs-model-backed review-risk hardening in the final Netflix branch

## What Is Already Strong

- Transcript-first canonical positioning is already repeated in `README.md`, `docs/current-status.md`, `docs/freeze-boundaries.md`, and the current demo-case READMEs.
- The Netflix branch progression is disciplined:
  - initial bounded panel
  - polish pass
  - final interpretation-hardening pass
- The final Netflix branch already demonstrates the most reusable reviewer-safety ideas:
  - interpretation rules up front
  - requested-path vs fallback-path distinctions
  - supporting-only caveats carried as persistent artifacts
  - heuristic visual output framed as context-only
  - disagreement framed as review priority rather than proof

## What Still Creates Reviewer Confusion

- `main` still had a few support-layer footguns before this pass:
  - downstream comparison crashed on nonblank-but-missing artifact paths
  - readiness output did not say how many downstream rows were actually target-comparable
  - rerun docs still used stale feature-worktree path wording
- Some reviewer-facing wording on `main` still read stronger than intended:
  - demo-path prose still said audio was "supportive"
  - planning docs still used `confidence` wording where `usability` or `quality-gated` was clearer
  - audio/visual summary notes still used `confidence uplift` wording even though those layers are reviewer context only
- `main` had no reusable validator for a reference-quality case package.
- The Netflix reference standard lived mostly in branch-specific docs and artifacts, not in a small reusable repo-native checklist.

## What Should Become Reusable Standard

- Required persistent package pieces:
  - asset audit
  - reviewed moment manifest
  - multimodal panel JSON + markdown
  - clip manifest
  - supporting-only caveats payload
  - disagreement and pressure subpanels when claimed
  - PR description + handoff summary
- Required interpretation rules:
  - deterministic transcript-backed outputs remain canonical
  - audio / NLP / visual layers are supporting-only reviewer context
  - heuristic visual output is context-only and non-adjudicative
  - missing or weak support stays explicit as unavailable / suppressed / skipped
  - disagreement is a review priority, not a winner/loser claim
- Required operational hygiene:
  - exact requested media path vs fallback media used must be stated
  - weak media must not be normalized into a stronger read
  - bounded-case work should happen on clean non-main branches or worktrees
- Required validation:
  - focused nearby tests
  - package-shape validation
  - `git diff --check`

## What Should Remain Case-Specific

- Moment ranking and top-8 showcase selection
- Company / quarter framing and reviewer notes
- Media path reality, fallback behavior, and exact usability caveats
- Which support layers are truly available for the case
- Pressure / disagreement panel contents
- Any case-specific clips, excerpts, or local operator notes

## Net Recommendation

- Treat `feat/netflix-reference-case-hardening` as the current gold reference for packaging and reviewer-safe framing.
- Keep `main` lean by standardizing only the reusable checklist, validator, honest readiness/comparison behavior, and nearby wording fixes.
- Build new bounded multimodal cases against that standard one case at a time rather than broadening into a general framework.
