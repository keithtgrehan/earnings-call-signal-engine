# Canonical Repo Hardening Summary

## What Was Audited

- Canonical repo: `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026`
- Active hardening worktree: `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-hardening`
- Legacy reference clone: `/Users/keith/GitHub/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026`
- Focus area: media-support evaluation, downstream comparison/readiness scaffolding, repo-name/path drift, and nearby tests/docs only

## What Was Found In The Old Clone

- Worth selectively porting:
  - a thin downstream comparison writer script that canonical did not yet have
- Already superseded in canonical:
  - stronger repo-relative path handling
  - honest treatment of rows without support targets
  - stricter comparison/eval tests
  - newer visual-trainability counts and surrounding readiness logic
- Not worth porting:
  - older eval/comparison implementations
  - older wording tied to stale visual-group counts
  - assumptions that every downstream row should be scored against support-direction targets

## What Was Ported

- Added `scripts/compare_multimodal_support_slice.py`
  - bounded CLI wrapper for the fixed downstream casepack
  - accepts repo-relative or absolute input/output paths
  - writes `downstream_decision_comparison.json` and `downstream_decision_comparison_rows.csv`
- Added `tests/test_media_support_scripts.py`
  - covers readiness-script downstream counts
  - covers the new comparison-script output writing path

## What Was Deliberately Not Ported

- No broad copy-over of legacy `media_support_eval.py`
- No broad copy-over of legacy `media_support_comparison.py`
- No broad copy-over of legacy readiness wording or stale assumptions
- No new cases, benchmarks, UI changes, or predictive/statistical claims

## Old Clone Rename Decision

- The old clone was not renamed.
- Reason:
  - it is on `codex/overnight/guidance-benchmark-batch`
  - it has tracked modifications and untracked media-support files in progress
  - renaming it during this pass would risk disrupting active local state

## Bugs, Docs, And Tests Fixed

- `scripts/check_media_support_readiness.py`
  - added a clearer visual-trainability note
  - added downstream casepack counts for rows with and without support targets
  - added top-level notes so readiness output is easier to read quickly
- `src/earnings_call_sentiment/media_support_comparison.py`
  - now treats missing nonblank artifact paths honestly instead of crashing
  - flags rows whose `metrics.json` bundle is not present locally
  - excludes those rows from current multimodal accuracy/error summaries
  - reports artifact coverage in the summary so reviewers can see how much of the casepack is actually comparable today
- `tests/test_media_support_comparison.py`
  - added coverage for missing nonblank `metrics.json` paths
- `tests/test_multimodal_support.py`
  - replaced a stale report-markdown test that was still asserting a removed multimodal-report signature
  - the test now checks the current deterministic report surface instead of expecting removed kwargs
- `data/media_support_eval/README.md`
  - added useful local commands
  - clarified that target-matching summaries apply only to rows with support targets
  - clarified that rows missing a current `metrics.json` bundle are flagged and excluded from current multimodal summary metrics
- `data/audio_signal_eval/README.md`
  - documented that `source_manifest.csv` still points at legacy-local normalized audio paths where canonical-local audio has not been rehydrated yet
- `docs/nlp-rerun-plan.md`
  - replaced stale `$FEAT_REPO` / feature-worktree wording with an explicit `LOCAL_REFERENCE_REPO` convention
- `docs/overnight_run_log_20260310.md`
  - added a note that the old repo path is historical context only after the repo rename

## Validation Commands Run

```bash
pytest -q tests/test_media_support_eval.py tests/test_media_support_comparison.py tests/test_media_support_scripts.py tests/test_multimodal_support.py
PYTHONPATH=src python3 scripts/check_media_support_readiness.py
PYTHONPATH=src python3 scripts/compare_multimodal_support_slice.py --help
PYTHONPATH=src python3 scripts/compare_multimodal_support_slice.py
git diff --check
```

## Validation Results

- `pytest ...` -> `16 passed in 2.87s`
- `scripts/check_media_support_readiness.py`
  - completed successfully
  - wrote `outputs/media_support_eval/media_support_readiness.json`
- `scripts/compare_multimodal_support_slice.py --help`
  - completed successfully
- `scripts/compare_multimodal_support_slice.py`
  - completed successfully
  - wrote:
    - `outputs/media_support_eval/downstream_decision_comparison.json`
    - `outputs/media_support_eval/downstream_decision_comparison_rows.csv`
- `git diff --check`
  - clean

## Known Limitations

- The canonical repo's primary checkout was already dirty on another branch, so this pass was executed from a fresh linked worktree created from clean `main`.
- The old clone remains in place because it is active/dirty and not safe to rename during this pass.
- `data/audio_signal_eval/source_manifest.csv` still points at legacy-local audio cache paths; this was documented rather than rewritten because the canonical-local audio files are not present today.
- The fixed downstream comparison casepack has 23 rows, but only 4 currently have a local `metrics.json` bundle available. The new summary now reports that coverage explicitly and excludes the other 5 labeled rows from current multimodal accuracy/error summaries.

## Recommended Next Steps After Review

- Review the new downstream comparison summary and rows output first to confirm the missing-bundle exclusion behavior reads clearly.
- Decide whether to rehydrate canonical-local audio cache assets before rewriting `data/audio_signal_eval/source_manifest.csv`.
- Decide whether to backfill more current `metrics.json` bundles for the fixed downstream casepack before treating comparison coverage as mature.
- Rename the old clone only after its active local branch/worktree state is no longer in use.
