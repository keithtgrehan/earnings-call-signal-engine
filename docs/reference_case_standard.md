# Reference Case Standard

This document defines the minimum bar for a bounded reviewer/demo case package.

## Core Rules

- Deterministic transcript-backed outputs remain canonical.
- Audio, NLP, and visual layers remain supporting-only reviewer context.
- Heuristic visual output must be context-only and non-adjudicative.
- Weak or missing support data must stay explicit as unavailable, suppressed, or skipped.
- No predictive-edge claims.
- No statistical-significance claims.
- One case at a time. Do not imply generalization from a single pack.

## Required Persistent Artifacts

For a case prefix such as `meta` or `netflix`, the reviewed package directory should include:

- `<prefix>_multimodal_moment_manifest.json`
- `<prefix>_multimodal_panel.json`
- `<prefix>_multimodal_panel.md`
- `<prefix>_clip_manifest.json`
- `<prefix>_supporting_only_caveats.json`
- one of:
  - `<prefix>_visual_support.json`
  - `<prefix>_visual_support_skipped.json`

Strongly preferred when claimed in docs or demos:

- `<prefix>_pressure_moments_panel.json`
- `<prefix>_disagreement_hotspots_panel.json`
- `<prefix>_model_comparison.json`
- `<prefix>_audio_support.json`

## Required Docs

- asset audit
- evidence panel markdown
- panel summary
- PR description
- handoff summary

## Required Panel JSON Content

- explicit case identifier:
  - `case_scope` or `case_id`
- non-empty moment rows:
  - `moments` or `panel_rows`
- explicit per-moment reviewer caveat text

Recommended for new packages:

- `deterministic_transcript_first_is_canonical`
- `support_layers_are_supporting_only`
- `no_predictive_claims`
- `no_statistical_claims`

## Required Caveat Coverage

Accepted layouts:

- flat caveat list with ids such as:
  - `transcript_first_canonical`
  - `support_layers_supporting_only`
  - `weak_or_missing_support_explicit`
  - `heuristic_visual_context_only`
  - `no_predictive_claims`
  - `no_statistical_claims`
- grouped legacy/reference map that clearly covers:
  - `deterministic`
  - `audio`
  - `visual`
  - `nlp_sidecars` when model comparison artifacts are present

## Minimum Quality Gates

- deterministic transcript-backed artifacts exist and are reviewable
- requested-path vs fallback-path media usage is documented exactly
- support-layer availability is explicit
- weak media is suppressed or skipped, not stretched
- heuristic visual output is labeled as context only when model-backed scoring is unavailable
- disagreement rows are framed as review priorities rather than proof or validation
- panel markdown tells reviewers how to read the pack before moment-level details

## Skip Behavior

- If visual analysis is not run or is not usable:
  - write `<prefix>_visual_support_skipped.json`
  - include `status: skipped`
  - include a non-empty reason
- If support layers are weak:
  - keep them explicit as unavailable or suppressed
  - do not silently convert them into neutral or same-direction support

## Acceptable Wording

- transcript-first
- canonical
- supporting-only
- reviewer context
- observational
- context-only
- quality-gated
- unavailable
- suppressed
- skipped
- review priority

## Unacceptable Wording

- confirms
- validates
- corroborates
- proves
- evidence for correctness
- high confidence in the read
- statistically significant
- predictive edge

## Validator

Use the repo-native validator on reviewed packages:

```bash
PYTHONPATH=src python3 scripts/validate_reference_case_package.py \
  --package-dir /abs/path/to/package \
  --prefix meta
```

## Handoff Summary Template

Every reference-quality case handoff should state:

- what was actually run
- what media was actually available
- whether requested media matched or fallback media was used
- what was skipped and why
- what reviewers should open first
- what remains heuristic or limited
- why the pack is bounded and reviewer-safe
- what should happen next only after review
