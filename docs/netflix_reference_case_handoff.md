# Netflix Reference Case Handoff

## What Was Run

- bounded Netflix manifest generation for `netflix_q1_2022`
- optional NLP sidecar comparison using `finbert_tone`, `financial_roberta`, `deberta_zero_shot`, and `mpnet_embeddings`
- reuse of the committed curated audio support rows for the aligned Q&A moments
- a bounded visual pass using the resolved local fallback Netflix MP4
- focused branch-relevant tests plus `git diff --check`

## Exact Commands

```bash
PYTHONPATH=src python3 scripts/build_netflix_multimodal_panel.py --device auto --visual-sample-fps 0.25
PYTHONPATH=src pytest -q tests/test_netflix_multimodal_panel.py tests/test_nlp_sidecars_config.py tests/test_nlp_sidecars_evaluate.py tests/test_nlp_sidecars_io.py tests/test_nlp_sidecars_runner.py tests/test_run_nlp_sidecars.py
git diff --check
```

## Media Actually Available

- requested exact local MP4 path:
  - `/Users/keith/Desktop/Netflix Meta Nvidia Capstone FINAL SOURCE/Netflix Q1 2022 Earnings Interview.mp4`
- resolved local MP4 actually used:
  - `/Users/keith/Desktop/Netflix Meta Nvidia Capstone FINAL SOURCE/Netflix/Netflix Q1 2022 Earnings Interview.mp4`
- repo-local source files available:
  - main earnings call transcript PDF
  - shareholder letter PDF
  - financial workbook and income-statement CSV
  - committed audio status and audio summary artifacts
- repo-local committed timed media support available:
  - curated Q&A audio windows reused in the final bundle
  - bounded visual windows for the same aligned Q&A answers

## What Was Skipped

- final persisted visual output:
  - not skipped
  - the bundle keeps a bounded heuristic-fallback visual artifact
- model-backed visual scoring:
  - unavailable
  - reason: the committed visual layer is heuristic fallback only and must remain context-only
- timed media coverage for some deterministic rows:
  - unavailable
  - affected rows include shareholder-letter and financial-anchor moments without timed media windows

## Outputs To Inspect First

- `docs/netflix_multimodal_asset_audit.md`
- `docs/netflix_multimodal_evidence_panel.md`
- `docs/netflix_multimodal_panel_summary.md`
- `data/demo_cases/netflix_q1_2022/demo/multimodal/netflix_multimodal_panel.json`
- `data/demo_cases/netflix_q1_2022/demo/multimodal/netflix_model_comparison.json`
- `data/demo_cases/netflix_q1_2022/demo/multimodal/netflix_disagreement_hotspots.json`
- `data/demo_cases/netflix_q1_2022/demo/multimodal/netflix_supporting_only_caveats.json`

## Known Limitations

- this is still a fixed Netflix Q1 2022 case, not a generalized multimodal framework
- audio remains limited to the curated Q&A windows already aligned in the repo
- the exact requested MP4 path did not match; the bounded visual pass used a fallback local MP4 instead
- the committed visual layer remains heuristic fallback only
- letter and financial-anchor rows still do not have timed media windows

## Why This Pack Is Bounded And Reviewer-Safe

- deterministic transcript-backed outputs remain canonical
- sidecars, audio, and visual remain supporting-only inspection layers
- the requested-path versus fallback-path distinction is explicit in the asset audit
- heuristic visual output stays visibly separate from any model-backed scoring claim
- disagreement rows are framed as review priorities, not proof or adjudication
- no predictive-edge or statistical-significance claims are made

## Recommendation After Review

- keep Netflix frozen as the reference-quality bounded case unless a future review finds a concrete truthfulness issue
- use this pack as the quality bar for later case ports only if the same transcript-first and supporting-only rules are preserved
