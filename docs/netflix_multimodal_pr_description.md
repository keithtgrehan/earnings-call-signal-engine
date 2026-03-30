# PR Title

Add bounded Netflix multimodal evidence panel

## Summary

Adds a bounded Netflix Q1 2022 multimodal review bundle plus the minimal supporting NLP sidecar plumbing needed to assemble and inspect it. Deterministic transcript-first outputs remain canonical throughout; NLP, audio, and video stay supporting-only reviewer context.

This PR is Netflix-case only for the multimodal bundle. It is intended for bounded demo/review use and possible later UI follow-up, not as a general multimodal rollout.

## What This Adds

- A fixed 11-moment Netflix multimodal review bundle with a top-8 showcase subset under `data/demo_cases/netflix_q1_2022/demo/multimodal/`.
- Reviewer-facing docs for the asset audit, evidence panel, and bundle summary under `docs/`.
- Pairwise NLP sidecar comparison outputs, disagreement hotspots, supporting-only caveats, and pressure/disagreement panel JSON shaped for later review or UI plumbing.
- A bounded visual pass tied only to curated timed Q&A windows when local video support is available.
- Small CLI/script support to build the Netflix bundle and keep optional NLP sidecar outputs additive rather than threaded into the canonical deterministic pipeline.

## What Stayed Intentionally Unchanged

- The deterministic transcript-backed Netflix demo artifacts remain the canonical review path.
- No canonical labels, deterministic outputs, or fixed demo payloads were redefined by sidecar output.
- No Meta case work was added to this branch delta.
- No general multimodal rollout, UI redesign, or schema expansion was introduced here.

## Guardrails / Claim Boundaries

- Deterministic transcript-first outputs remain canonical.
- NLP sidecars, audio cues, and visual cues are supporting-only.
- This bundle is limited to the Netflix Q1 2022 case.
- The visual pass is bounded and observational; the committed bundle used a fallback local Netflix MP4 after the exact requested path did not match.
- The current visual support is heuristic fallback only, not model-backed visual scoring.
- No predictive, alpha, lift, or statistical-significance claims are made.

## Testing Performed

- `pytest -q tests/test_netflix_multimodal_panel.py tests/test_nlp_sidecars_io.py`
- `PYTHONPATH=src python3 scripts/build_netflix_multimodal_panel.py --help`

## Reviewer Checklist

- Confirm the PR keeps deterministic transcript-backed outputs canonical.
- Confirm sidecars/audio/video are framed as supporting-only everywhere reviewer-facing.
- Confirm the multimodal bundle is scoped to Netflix Q1 2022 only.
- Confirm the asset audit clearly distinguishes requested MP4 path vs fallback local MP4 used.
- Confirm no predictive or statistical claims slipped into docs, JSON, or README language.
- Confirm the reusable NLP sidecar plumbing is additive support for this bounded bundle, not a hidden rewrite of the canonical path.

## Out Of Scope Follow-Up Ideas

- UI surfacing for the top-8 showcase and pressure/disagreement panels.
- Any broader multimodal rollout beyond the Netflix case.
- Any model-backed visual scoring upgrade beyond the current bounded heuristic fallback.
- Any claims about predictive value, lift, or human-study validation.
