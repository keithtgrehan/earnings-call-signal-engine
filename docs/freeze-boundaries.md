# Freeze Boundaries

This repo is currently under a narrow freeze for the transcript-first deterministic core, the benchmark packages, and public claim language. Changes inside these boundaries should only happen to fix a real bug, corruption issue, or documented inconsistency.

## Frozen Core Files
The deterministic transcript-first review logic currently lives primarily in:

- `src/earnings_call_sentiment/cli.py`
  Guidance extraction, guidance revision comparison, and the core deterministic artifact-writing path.
- `src/earnings_call_sentiment/signals/behavior.py`
  Deterministic behavior rules for uncertainty, reassurance, and analyst skepticism.
- `src/earnings_call_sentiment/signals/qa_shift.py`
  Deterministic prepared-remarks vs Q&A shift summaries.
- `src/earnings_call_sentiment/review_scorecard.py`
  Deterministic scorecard presentation derived from existing transcript-backed artifacts.
- `src/earnings_call_sentiment/postprocess.py`
  Transcript-backed postprocessing outputs such as `sentiment_segments.csv` and `risk_metrics.json`.

These files should be treated as frozen unless a real bug is identified and explained.

## Frozen Benchmark Assets
The canonical benchmark and review packages that should be treated as frozen are:

- `data/gold_guidance_calls/`
  Canonical package for the frozen gold benchmark.
  Canonical files:
  `labels.csv`, `call_manifest.csv`, `official_source_manifest.csv`, `prior_quarter_sources.csv`, `transcript_inventory.csv`, `transcription_status.csv`, and `raw_calls/*.txt`
- `data/gold_guidance_calls_holdout/`
  Active unseen holdout package.
  Canonical files:
  `labels.csv`, `call_manifest.csv`, `official_source_manifest.csv`, `transcription_status.csv`, and `raw_calls/*.txt`
- `data/gold_guidance_calls_holdout_watchlist/`
  Watchlist-derived holdout package.
  Canonical files:
  `labels.csv`, `call_manifest.csv`, `official_source_manifest.csv`, `transcription_status.csv`, and `raw_calls/*.txt`
- `data/behavior_signal_eval/`
  Behavior rule-QA package.
  Canonical files:
  `source_manifest.csv`, `uncertainty_labels.csv`, `reassurance_labels.csv`, and `skepticism_labels.csv`

Within `data/gold_guidance_calls/`, `draft_labels.csv` and `draft_label_review.md` should be treated as archival working materials rather than current public-label sources.

## Allowed Public Claims
Allowed public positioning is limited to:

- a transcript-first validated prototype
- a deterministic evidence-backed review tool
- strong internal agreement checkpoints on the frozen benchmark and holdout packages
- multimodal sidecars that are supporting, partial, and non-canonical

## Explicitly Not Claimed
The repo does not currently claim:

- statistical significance
- trading edge or return advantage
- autonomous trading capability
- finance-wide generalization from the current benchmark package
- proven predictive improvement from multimodal sidecars
- proven visual-model quality or psychological inference capability

## Interpretation Rule
If a wording choice goes beyond the claims above, soften it or restate it as design intent, reviewer workflow support, or internal agreement evidence rather than proven user or market impact.
