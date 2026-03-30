# Legacy Clone Salvage Report

## Scope

- Canonical repo audited: `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026`
- Legacy reference repo audited: `/Users/keith/GitHub/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026`
- Comparison focus: media-support evaluation, readiness, downstream comparison scaffolding, and nearby tests/docs only

## Worth Porting

- `scripts/compare_multimodal_support_slice.py`
  - The legacy clone had a small, useful downstream comparison writer that canonical did not yet carry.
  - It was ported selectively into canonical, with light hardening so it now accepts repo-relative or absolute paths and writes the same bounded comparison outputs in a cleaner CLI wrapper.

## Already Superseded In Canonical

- `src/earnings_call_sentiment/media_support_comparison.py`
  - Canonical is stronger because it resolves repo-relative artifact paths, handles unscored / missing support-target rows honestly, and reports case counts with and without support targets.
- `scripts/check_media_support_readiness.py`
  - Canonical already superseded the legacy version by adding downstream case coverage into the readiness summary instead of only counting total downstream rows.
- `src/earnings_call_sentiment/media_support_eval.py`
  - Canonical already keeps the same visual trainability `minimum_next_data` logic while sitting on a newer labeled set and stronger surrounding tests.
- `tests/test_media_support_eval.py`
  - Canonical already uses stricter, more current tests around seed-file counts, repo-relative casepack paths, and the current visual-group status.
- `tests/test_media_support_comparison.py`
  - Canonical already superseded the legacy tests with explicit coverage for repo-relative artifact paths and honest handling of unscored downstream rows.

## Not Worth Porting

- Direct copy-over of legacy media-support eval, comparison, or readiness files
  - The legacy versions are older and would regress canonical’s honesty improvements if copied wholesale.
- Legacy wording that assumed a single visual group remained
  - Canonical now reflects the newer two-group visual state and should not be rolled back to older counts.
- Any legacy assumptions that all downstream rows should be scored against support-direction targets
  - Canonical is more truthful because it keeps rows without support targets explicitly unscored.

## Risky / Stale / Weaker In The Old Clone

- The legacy clone itself is not safe to rename right now.
  - It is on `codex/overnight/guidance-benchmark-batch`.
  - It has tracked modifications and untracked media-support files/scripts in progress.
  - Renaming it during this pass would risk breaking an active local worktree state.
- The legacy clone still carries path assumptions tied to its own local checkout.
  - That is fine for historical reference, but it should not be treated as canonical guidance for new work.
- The legacy clone’s missing repo-relative-path safeguards are weaker than canonical.
  - In particular, canonical now handles repo-relative downstream artifact paths cleanly, which is safer for reviewers and future reruns.

## Net Decision

- Ported: one small bounded downstream comparison script.
- Kept canonical as-is for the main media-support eval/comparison/readiness logic because it is already stronger.
- Left the legacy clone in place and documented it as reference-only because its current local state is not safe to rename in this pass.
