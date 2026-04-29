# Repo Review Cleanup Report

## Repo / Branch / Commit Reviewed

- Repo: `/Users/keith/Documents/New project/earnings-call-signal-engine-support-qa`
- Remote: `git@github.com:keithtgrehan/earnings-call-signal-engine.git`
- Branch: `signal-engine-2.0`
- Starting commit reviewed: `e4d0954 chore: add model dataset and weak baseline readiness`
- Local branch status after fetch: `signal-engine-2.0`; `origin/main` advanced independently and was not merged.

## Files Reviewed

- `README.md`
- `docs/*.md` through the markdown link checker
- `scripts/*.py` through `py_compile`
- Focused tests for corpus validation, gold-label validation, evaluation output comparison, model registry validation, training-set registry validation, weak-label baseline, and optional sklearn smoke scaffolding
- Example registries and manifests in `data/`
- Tracked file-size surface through `git ls-files`

## Changes Made

- Rewrote `README.md` into a current Signal Engine 2.0 guide.
- Added this cleanup report.
- Kept the README focused on what works now, what is scaffolded only, what is not proven, and how to run lightweight validation.
- Added direct quickstart commands for corpus manifest validation, model/dataset registry validation, weak-label baseline use, manual corpus intake, and SEC metadata intake.
- Linked the current evaluation-readiness docs required for the branch.

## Bugs Fixed

- No code bugs were found in the recent scaffold validation path.
- No `src/signal_engine` changes were needed.
- No script syntax/import-path issues were found by `py_compile`.
- No markdown links were broken in README or docs.

## README / Docs Alignment Changes

- Removed stale README emphasis on older proof-package workflows as the main entry point.
- Clarified that registries, weak labels, handcrafted fixtures, and sklearn smoke tests are scaffolds only.
- Clarified that no production ML, statistical significance, validated retrieval, market correlation, or full real corpus is claimed.
- Made the 30 manually reviewed real earnings calls the explicit next credibility milestone.

## Commands Run

```bash
pwd
git rev-parse --show-toplevel
git remote -v
git branch --show-current
git status --short
git log --oneline -8
git diff --stat
find . -maxdepth 3 -type f | sort | sed 's#^\./##' | head -400
git fetch origin
git status -sb
git ls-files -z | xargs -0 du -k | sort -nr | head -30
python scripts/validate_model_registry.py --help
python scripts/validate_training_sets_registry.py --help
python scripts/run_weak_label_baseline.py --help
python scripts/train_text_classifier_baseline.py --help
python scripts/fetch_sec_8k_index.py --help
python scripts/build_manual_corpus_case.py --help
python -m py_compile scripts/*.py
python -m pytest tests/test_validate_corpus_manifest.py tests/test_validate_gold_labels.py tests/test_evaluate_signal_outputs.py tests/test_validate_model_registry.py tests/test_validate_training_sets_registry.py tests/test_run_weak_label_baseline.py tests/test_train_text_classifier_baseline_smoke.py -q
python scripts/check_markdown_links.py README.md docs/*.md
python scripts/validate_corpus_manifest.py --path data/corpus_manifest.example.csv
python scripts/validate_corpus_manifest.py --path data/corpus_manifest.example.json
python scripts/validate_gold_labels.py --path data/gold_labels.example.jsonl
python scripts/validate_model_registry.py --path data/model_registry.example.json
python scripts/validate_training_sets_registry.py --path data/training_sets_registry.example.csv
python scripts/validate_training_sets_registry.py --path data/training_sets_registry.example.json
python scripts/run_weak_label_baseline.py --input tests/fixtures/tiny_realistic_earnings_excerpt.txt --case-id TEST_2026_Q1 --out /tmp/tiny_predictions.jsonl
python scripts/evaluate_signal_outputs.py --gold-labels data/gold_labels.example.jsonl --predictions /tmp/tiny_predictions.jsonl --report-out /tmp/tiny_eval.md --json-out /tmp/tiny_eval.json
git diff --stat
git status --short
```

## Validation Results

- `python -m py_compile scripts/*.py`: passed.
- Focused pytest command: passed, `22 passed`.
- `python scripts/check_markdown_links.py README.md docs/*.md`: passed.
- Corpus CSV manifest validation: passed, 8 rows.
- Corpus JSON manifest validation: passed, 8 rows.
- Gold-label example validation: passed, 7 rows.
- Model registry validation: passed, 13 rows.
- Training-set registry CSV validation: passed, 15 rows.
- Training-set registry JSON validation: passed, 15 rows.
- Weak-label baseline fixture run: passed, 6 deterministic predictions.
- Evaluator compatibility run: passed, with 0 matched, 7 unmatched, and 6 potential false positives because the weak-label fixture uses `TEST_2026_Q1`, not the example gold-label case IDs.

## Remaining Known Issues

- Some legacy generated or processed artifacts are already tracked, including demo PDFs, processed transcript outputs, and small model artifacts under `models/media_support/`. They were not introduced in this cleanup pass and were intentionally not deleted.
- `origin/main` advanced during `git fetch origin`; it was not merged into `signal-engine-2.0`.
- Full broad pytest was not run because the requested focused validation passed and the branch has known legacy surfaces that can be slower/noisier.
- The SEC intake script is metadata-only and was not run against SEC during validation to avoid unnecessary network/data acquisition.

## Intentionally Not Touched

- `src/signal_engine/`
- Legacy proof artifact directories
- Raw transcript/demo case assets already in history
- Model artifact files already in history
- GitHub workflows and CI configuration
- Retrieval, embeddings, rerankers, long-context review, ASR, diarization, audio, and video implementation paths

## Next Recommended Task

Create a real working 30-call corpus manifest from `docs/ideal-30-call-download-list.md`, manually confirm the first source, then scaffold the first case folder with:

```bash
python scripts/build_manual_corpus_case.py --manifest data/corpus_manifest.example.csv --case-id NVDA_2026_Q4 --out-root /tmp/manual_cases
```

After manual source confirmation and legally safe transcript handling, add reviewer-owned labels and run the existing validators before any benchmark or model claims.
