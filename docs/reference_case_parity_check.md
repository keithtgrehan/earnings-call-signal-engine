# Reference Case Parity Check

## What Is Structurally Aligned

- Both Netflix and Meta persist the same core artifact family:
  - moment manifest
  - multimodal panel JSON and markdown
  - model comparison
  - disagreement hotspots
  - pressure panel
  - audio support
  - clip manifest
  - supporting-only caveats
  - visual status artifact
- Both packs lead with transcript-first interpretation rules before moment-level detail.
- Both packs frame disagreement hotspots as review priorities rather than proof.
- Both packs use the same reviewer-note style: deterministic read first, supporting layers second, explicit caveat last.
- Both packs keep pressure and disagreement subpanels under the same artifact names and `rows` payload shape.

## What Differs Intentionally

- Netflix persists `netflix_visual_support.json` because it has a bounded heuristic visual pass; Meta persists `meta_visual_support_skipped.json` because the final visual pass was intentionally skipped.
- Netflix uses the legacy grouped caveat map (`deterministic`, `audio`, `visual`, `nlp_sidecars`); Meta uses the newer flat caveat id list. The validator accepts both layouts.
- Netflix uses a fallback local MP4 path; Meta matched the exact requested MP4 path directly.
- Netflix includes active heuristic visual reviewer notes; Meta now carries an explicit visual skip instead of pretending to have moment-level visual observations.

## What Differed Accidentally And Was Fixed

- Meta originally let the final visual skip collapse into generic per-moment `unavailable` wording on some downstream surfaces. This pass preserved the case-level skip explicitly for timestamped main-call moments and called it out in reviewer notes.
- Meta originally made the top-8 showcase auditable only through per-row booleans. This pass added an explicit `top_8_showcase_moment_ids` list.
- Meta originally lacked panel-level canonical/supporting-only flags. This pass added explicit panel-level booleans so the standard is easier to verify directly from the persisted panel payload.

## What Remains Case-Specific By Design

- Moment ids, ranking, and the top-8 selection.
- The exact deterministic categories and reviewer notes.
- Which moments have timed main-call media windows.
- Whether the visual artifact is a bounded heuristic output or an honest skip.
- Which optional sidecar models were actually persisted in the final pack.
