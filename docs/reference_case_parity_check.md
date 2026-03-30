# Reference Case Parity Check

## What Was Checked

- Netflix branch:
  - `data/demo_cases/netflix_q1_2022/demo/multimodal/netflix_multimodal_panel.json`
  - `data/demo_cases/netflix_q1_2022/demo/multimodal/netflix_multimodal_panel.md`
  - `data/demo_cases/netflix_q1_2022/demo/multimodal/netflix_model_comparison.json`
  - `data/demo_cases/netflix_q1_2022/demo/multimodal/netflix_disagreement_hotspots.json`
  - `data/demo_cases/netflix_q1_2022/demo/multimodal/netflix_pressure_moments_panel.json`
- Meta branch:
  - `data/demo_cases/meta_q3_2022/demo/multimodal/meta_multimodal_panel.json`
  - `data/demo_cases/meta_q3_2022/demo/multimodal/meta_multimodal_panel.md`
  - `data/demo_cases/meta_q3_2022/demo/multimodal/meta_model_comparison.json`
  - `data/demo_cases/meta_q3_2022/demo/multimodal/meta_disagreement_hotspots.json`
  - `data/demo_cases/meta_q3_2022/demo/multimodal/meta_pressure_moments_panel.json`
- Branch-local docs describing each persisted pack
- The shared reference-case validator expectations

## Issues Found

- Meta already exposed panel-level canonical/supporting-only flags, `case_scope`, explicit top-8 ids, and case-level visual status in its persisted panel payloads.
- Netflix still relied on row-level caveats and summary docs for the same contract, which made the two reference cases less directly comparable than they should be.
- Netflix comparison, disagreement, and pressure subpanel payloads also lacked `case_scope`, which made structural parity checks unnecessarily indirect.
- Netflix did have a handoff doc, but it did not use the same explicit `what ran` / `media available` / `what was skipped` / `open first` / `limitations` structure already used by Meta, which left the handoff requirement satisfied only indirectly.

## What Was Corrected

- On `feat/netflix-reference-case-hardening`, the Netflix persisted payloads were hardened to expose:
  - `case_scope`
  - `deterministic_transcript_first_is_canonical`
  - `support_layers_are_supporting_only`
  - `no_predictive_claims`
  - `no_statistical_claims`
  - `top_8_showcase_moment_ids`
  - `visual_support_status`
  - `visual_support_reason`
- Netflix `model_comparison`, `disagreement_hotspots`, `pressure_moments_panel`, and `disagreement_hotspots_panel` now also carry `case_scope`.
- The persisted Netflix panel JSON was regenerated from the existing bounded bundle artifacts so the checked-in reference pack matches the safer schema.
- The Netflix handoff doc was rewritten into an explicit handoff summary structure so it now states:
  - what actually ran
  - what media was actually available
  - what was skipped versus merely unavailable
  - what reviewers should open first
  - what remains limited or heuristic
  - why the pack remains bounded and reviewer-safe

## What Remains Acceptable But Worth Reviewer Attention

- Netflix still uses the legacy grouped caveat payload shape while Meta uses the flat id-list caveat payload. The shared validator accepts both, and both remain reviewer-safe.
- Netflix persists a bounded heuristic-fallback visual artifact with `status: ok`; Meta persists an explicit case-level visual skip artifact with `status: skipped`. This is an intentional case difference, not a parity bug.
- Meta uses `strong_supporting_context_moments` while Netflix still exposes `cleaner_sidecar_examples`. The intent is similar, but the field names are not yet identical.
- Netflix still uses the filename `docs/netflix_reference_case_handoff.md` while Meta uses `docs/meta_multimodal_handoff_summary.md`. The content gap is corrected; the filename difference is acceptable for now.
- Markdown structure is already materially aligned across the two cases and did not require further changes in this pass.

## Exact Commands Run

```bash
git worktree list --porcelain
rg --files docs | rg 'netflix.*handoff|handoff.*netflix|netflix.*summary'
python3 - <<'PY'
import json
from pathlib import Path
meta_base = Path('/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-meta-reference-case/data/demo_cases/meta_q3_2022/demo/multimodal')
net_base = Path('/Users/keith/Documents/New project/main-demo-wt/data/demo_cases/netflix_q1_2022/demo/multimodal')
for stem in ['multimodal_panel.json', 'model_comparison.json', 'disagreement_hotspots.json', 'pressure_moments_panel.json']:
    meta = json.loads((meta_base / f'meta_{stem}').read_text())
    net = json.loads((net_base / f'netflix_{stem}').read_text())
    print(stem, sorted(meta.keys()), sorted(net.keys()))
PY
PYTHONPATH=src pytest -q tests/test_netflix_multimodal_panel.py
PYTHONPATH="/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-reference-standardization/src" python3 "/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-reference-standardization/scripts/validate_reference_case_package.py" --package-dir "/Users/keith/Documents/New project/main-demo-wt/data/demo_cases/netflix_q1_2022/demo/multimodal" --prefix netflix
git diff --check
```

## Tests Run And Results

- Netflix parity-related regression:
  - `PYTHONPATH=src pytest -q tests/test_netflix_multimodal_panel.py`
  - result: `13 passed`
- Shared validator against the corrected Netflix package:
  - result: `valid: true`
- `git diff --check`
  - result: clean in the touched worktrees at verification time

## Branch Status

- Cross-case parity audit doc added on `chore/reference-case-standardization`
- Netflix structural parity fix landed on `feat/netflix-reference-case-hardening`
- Meta branch required no additional correction in this pass
