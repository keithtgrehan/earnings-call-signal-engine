# PR Title

Harden Netflix multimodal reference demo case

## Summary

Tightens the existing Netflix Q1 2022 multimodal bundle so it reads as the repo's reference-quality bounded demo case. Deterministic transcript-backed outputs remain canonical throughout. NLP sidecars, audio cues, and visual cues remain supporting-only inspection layers.

This is Netflix-case only. It is for bounded demo/review use and possible later UI follow-up, not a general multimodal rollout and not proof of generalization.

## What This Changes

- Hardens reviewer-facing terminology across docs and persisted JSON so the supporting layers are harder to overread.
- Makes mixed sidecar rows explicit by replacing implied consensus with a leading-label / tied-label read.
- Renames low-risk persisted fields away from confidence, support, and alignment wording where those names could sound stronger than intended.
- Adds blunt interpretation rules in the primary reviewer docs and README.
- Keeps the visual layer unmistakably marked as heuristic fallback only, not model-backed scoring.

## What Stayed Intentionally Unchanged

- The deterministic transcript-backed Netflix demo artifacts remain the canonical review path.
- No canonical labels or deterministic outputs were redefined by sidecar output.
- No new companies, cases, models, benchmarks, or UI redesign were added here.
- The reusable sidecar plumbing remains additive support for this bounded Netflix pack only.

## Guardrails / Claim Boundaries

- Deterministic transcript-first outputs remain canonical.
- NLP sidecars, audio cues, and visual cues are supporting-only inspection layers.
- This bundle is limited to the Netflix Q1 2022 case.
- The visual pass is bounded and observational; the committed bundle used a fallback local Netflix MP4 after the exact requested path did not match.
- The current visual layer is heuristic fallback only, not model-backed visual scoring.
- Disagreement rows are ranked for review priority only; they do not prove anything and do not override the transcript-backed read.
- No predictive, alpha, lift, or statistical-significance claims are made.
- This branch makes the Netflix case reference-quality for this repo; it does not claim that the same result generalizes to Nvidia, Meta, or any broader rollout.

## Testing Performed

- `pytest -q tests/test_netflix_multimodal_panel.py tests/test_nlp_sidecars_config.py tests/test_nlp_sidecars_evaluate.py tests/test_nlp_sidecars_io.py tests/test_nlp_sidecars_runner.py tests/test_run_nlp_sidecars.py`
- `PYTHONPATH=src python3 scripts/build_netflix_multimodal_panel.py --help`

## Reviewer Checklist

- Confirm the PR keeps deterministic transcript-backed outputs canonical.
- Confirm NLP/audio/video are framed as supporting-only everywhere reviewer-facing.
- Confirm the bundle remains Netflix Q1 2022 only.
- Confirm the asset audit clearly distinguishes the requested MP4 path from the fallback local MP4 actually used.
- Confirm the visual layer is explicitly marked as heuristic fallback only, not model-backed scoring.
- Confirm mixed sidecar rows no longer imply consensus where the comparable labels are tied.
- Confirm no predictive or statistical claims slipped into docs, JSON, or README language.
- Confirm the branch reads like a bounded reference case, not a general multimodal claim.

## Out Of Scope Follow-Up Ideas

- UI surfacing for the top-8 showcase and pressure/disagreement panels.
- Any broader multimodal rollout beyond the Netflix case.
- Any model-backed visual scoring upgrade beyond the current bounded heuristic fallback.
- Any claims about predictive value, lift, significance, or human-study validation.
