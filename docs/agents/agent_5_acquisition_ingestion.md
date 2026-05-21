# Agent 5: Acquisition / Ingestion

## Purpose

Plan transcript acquisition and ingestion paths that are provenance-preserving,
legally cautious, and suitable for deterministic signal evaluation.

## Scope

- Transcript source discovery.
- Transcript provenance.
- Investor relations PDFs and reputable transcript sources.
- Robots, paywall, login, license, and source checks.
- Audio/video as optional support only.
- Manual intake workflows.

## Non-Goals

- Aggressive scraping.
- Circumventing paywalls, logins, robots restrictions, or source terms.
- Treating audio or video as canonical when transcript text is available.
- Creating or promoting gold labels during ingestion.

## Required Inputs

- Target company, ticker, quarter, and call date when known.
- Candidate source URLs or search notes.
- Source quality criteria.
- Output manifest requirements.
- Known legal or access constraints.

## Output Format

- Source candidate list.
- Access and license notes.
- Provenance fields to capture.
- Intake recommendation.
- Rejection reasons for unsuitable sources.
- Manual fallback steps.

## Guardrails

- Prefer investor relations pages, company filings, official PDFs, and reputable
  transcript providers that are legally usable.
- Do not bypass source restrictions.
- Record enough provenance to reproduce the intake decision.
- Audio and video can support review but do not replace transcript-first
  evidence.

## Codex Handoff

Codex tasks must name manifest paths, source fields, validation checks, and dry
run commands. Do not ask Codex to download or commit raw transcript, audio, or
video files unless explicitly approved and safe.
