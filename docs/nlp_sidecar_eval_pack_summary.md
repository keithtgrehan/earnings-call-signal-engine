# NLP Sidecar Eval Pack Summary

Branch: `feat/nlp-sidecar-eval-pack`

## What changed
- Added a dedicated optional `src/earnings_call_sentiment/nlp_sidecars/` package instead of threading sidecar behavior through the canonical deterministic pipeline.
- Added a standalone runner script, `scripts/run_nlp_sidecars.py`, with `run` and `compare` commands.
- Added repo-artifact loaders for exactly these unit types:
  - `chunks`
  - `guidance_spans`
  - `qa_answers`
- Added per-model output writing under `outputs/<case_id>/model_sidecars/<model_name>/` with:
  - `scored_rows.csv`
  - `run_summary.json`
  - `model_metadata.json`
  - `summary.md`
  - `disagreement_report.json`
  - `embeddings.json` for embedding runs
- Added rolled-up per-case comparison outputs under `outputs/<case_id>/model_sidecars/evaluation/`.
- Added focused tests for config loading, artifact loading, runner behavior, graceful dependency failures, output writing, and compare-script invocation.

## Models wired
- `finbert_tone`
  Model id: `yiyanghkust/finbert-tone`
- `financial_roberta`
  Model id: `soleimanian/financial-roberta-large-sentiment`
- `deberta_zero_shot`
  Model id: `MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli`
  Label configs: [configs/nlp_sidecars/zero_shot_labels.default.json](/Users/keith/Documents/New%20project/main-demo-wt/configs/nlp_sidecars/zero_shot_labels.default.json), [configs/nlp_sidecars/zero_shot_labels.finance.json](/Users/keith/Documents/New%20project/main-demo-wt/configs/nlp_sidecars/zero_shot_labels.finance.json)
- `mpnet_embeddings`
  Model id: `sentence-transformers/all-mpnet-base-v2`
  Use is limited to similarity / disagreement inspection only.

## What sidecars do
- Add optional supporting model outputs over existing repo artifacts.
- Surface disagreement hotspots versus deterministic labels when a reasonable polarity comparison exists.
- Summarize runtime, units covered, and pairwise model differences.

## What sidecars do not do
- They do not replace transcript-backed deterministic outputs.
- They do not claim predictive lift, trading edge, or statistical significance.
- They do not treat embeddings as sentiment truth.
- They do not treat zero-shot outputs as finance ground truth.
- They do not broaden the canonical parser or rewrite existing deterministic artifacts.

## How to run
Example full reduced run against a packaged demo case:

```bash
PYTHONPATH=src python scripts/run_nlp_sidecars.py run \
  --case-id meta_q3_2022 \
  --demo-case-root data/demo_cases/meta_q3_2022 \
  --models finbert_tone financial_roberta \
  --units chunks guidance_spans qa_answers \
  --smoke-limit 4 \
  --prewarm
```

Refresh comparison summaries only:

```bash
PYTHONPATH=src python scripts/run_nlp_sidecars.py compare --case-id meta_q3_2022
```

## CPU vs GPU expectations
- CPU is workable for `finbert_tone`, `financial_roberta`, and smaller `mpnet_embeddings` subsets.
- `deberta_zero_shot` is much slower on CPU and is best treated as subset/smoke validation without GPU.
- The runner supports explicit `--device auto|cpu|cuda`, cache-aware prewarm, and resume/skip behavior for successful prior outputs.

## What was actually validated overnight
Completed branch-local real-case reduced runs:
- `meta_q3_2022`
  Models: `finbert_tone`, `financial_roberta`
  Units: `chunks`, `guidance_spans`, `qa_answers`
  Smoke limit: `4`
  Runtime:
  `finbert_tone` `1.8222s`
  `financial_roberta` `6.4788s`
- `nvidia_q4_fy2024`
  Models: `finbert_tone`, `deberta_zero_shot`
  Units: `guidance_spans`, `qa_answers`
  Smoke limit: `3`
  Runtime:
  `finbert_tone` `0.7847s`
  `deberta_zero_shot` `38.8309s`
- `netflix_q1_2022`
  Models: `mpnet_embeddings`
  Units: `guidance_spans`, `qa_answers`
  Smoke limit: `2`
  Runtime:
  `mpnet_embeddings` `1.0722s`

These were reduced local validation runs only. They show that the pack is wired and can complete on real repo artifacts; they do not establish model quality claims.

## Tests passed
- `pytest tests/test_nlp_sidecars_config.py tests/test_nlp_sidecars_io.py tests/test_nlp_sidecars_runner.py tests/test_nlp_sidecars_evaluate.py tests/test_run_nlp_sidecars.py`
  Result: `8 passed`
- `pytest tests/test_nlp_sidecars_evaluate.py tests/test_nlp_sidecars_runner.py tests/test_run_nlp_sidecars.py`
  Result: `4 passed`
- `pytest tests/test_imports.py tests/test_cli_help.py tests/test_review_workflow.py`
  Result: `5 passed`
- `python -m compileall src/earnings_call_sentiment/nlp_sidecars scripts/run_nlp_sidecars.py`
  Result: completed successfully

## What was intentionally left out
- No changes to the main deterministic CLI flow.
- No attempt to score `speaker_turns`; that would have required broader parsing/risk.
- No accuracy or benchmark-quality claims.
- No committed claim that every model is practical for full-call CPU runs.
- No attempt to merge in the larger model-sidecar branches; this pack is intentionally narrower and cleaner.

## What should be reviewed first
- [scripts/run_nlp_sidecars.py](/Users/keith/Documents/New%20project/main-demo-wt/scripts/run_nlp_sidecars.py)
- [src/earnings_call_sentiment/nlp_sidecars/runner.py](/Users/keith/Documents/New%20project/main-demo-wt/src/earnings_call_sentiment/nlp_sidecars/runner.py)
- [src/earnings_call_sentiment/nlp_sidecars/io.py](/Users/keith/Documents/New%20project/main-demo-wt/src/earnings_call_sentiment/nlp_sidecars/io.py)
- [src/earnings_call_sentiment/nlp_sidecars/models.py](/Users/keith/Documents/New%20project/main-demo-wt/src/earnings_call_sentiment/nlp_sidecars/models.py)
- [src/earnings_call_sentiment/nlp_sidecars/evaluate.py](/Users/keith/Documents/New%20project/main-demo-wt/src/earnings_call_sentiment/nlp_sidecars/evaluate.py)

## What remains incomplete
- The new pack currently prefers explicit artifact paths or demo-case roots; it does not yet infer every possible historical output layout.
- Pairwise model comparison is strongest when models expose comparable polarity labels. Zero-shot exact label agreement is still inherently noisier because label spaces differ.
- Embedding output is wired and validated on reduced subsets, but similarity hotspot reporting should still be treated as exploratory reviewer support.

## Next best merge candidate after this branch
- `codex/hardening-batch-runbook`

It still looks like the best next bounded technical branch after this one because it improves execution reliability without threatening the transcript-first review boundary.
