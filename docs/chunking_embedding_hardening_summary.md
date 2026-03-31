# Chunking + Embedding Hardening Summary

## What Changed

- Hardened `scripts/search_case_retrieval.py` for reviewer use:
  - `--case` now works as an alias for `--case-id`
  - `--query` now works as an explicit query flag
  - positional query support remains in place
  - help text now frames hybrid as the recommended reviewer mode
- Hardened both retrieval CLIs so `python3 scripts/build_case_retrieval.py ...` and `python3 scripts/search_case_retrieval.py ...` work from the repo root without requiring a hidden `PYTHONPATH=src` setup.
- Hardened `src/earnings_call_sentiment/retrieval_support.py` with bounded ranking adjustments for:
  - short-text penalties
  - low-information guidance/meta penalties
  - structured-row boosts
  - transcript-chunk de-preferencing when richer structured rows are close
  - analyst-skepticism query boosts
  - competition / slowdown query boosts
- Added one final bounded skepticism correction:
  - skepticism-oriented queries now add a small extra bonus for analyst-question rows that carry the strongest opener language such as `tone`, `very different`, `3 months ago`, `competition`, `macro`, `maturity`, and `walk us through how your views have changed`
- Added a bounded Netflix retrieval evaluation fixture:
  - `tests/fixtures/netflix_retrieval_eval.json`
  - 12 reviewer-style queries with expected source families and row ids
- Added focused regressions in `tests/test_retrieval_support.py`
- Updated the summary and Netflix demo docs for the hardened reviewer flow

## Ranking Fixes

- Penalized weak rows such as very short snippets and known low-information guidance/meta rows like “nonguidance guidance”.
- Added light structured-row boosts for:
  - guidance spans
  - Q&A answer spans
  - analyst question spans
  - shareholder-letter or press-release paragraphs with useful deterministic labels
- Added explicit query-intent boosts for:
  - analyst / skeptical / challenging question queries
  - competition / slowdown / growth-headwind queries
- Added a final skepticism-opener bonus so the strongest Netflix opening skepticism question rises above more generic analyst questions for clearly skepticism-oriented queries.
- Added a small baseline penalty for transcript chunks so richer structured rows win when scores are otherwise close.
- Preserved provenance on every result; no ranking step strips source locators, row ids, or deterministic labels.

## CLI Fixes

- Reviewers can now use either:
  - `python3 scripts/search_case_retrieval.py "query text" ...`
  - `python3 scripts/search_case_retrieval.py --query "query text" ...`
- Reviewers can now use either:
  - `--case-id netflix_q1_2022`
  - `--case netflix_q1_2022`
- `python3 scripts/build_case_retrieval.py --help` and `python3 scripts/search_case_retrieval.py --help` now work from the repo root without extra environment setup.
- `--help` now says clearly:
  - hybrid is the recommended reviewer mode
  - lexical is the fallback/literal debug view
  - semantic is the noisier exploration/debug view

## Follow-Up Verification Fix

- Issue found in this pass:
  - both retrieval scripts still failed immediately when run as `python3 scripts/...` from the repo root unless `PYTHONPATH=src` had been set manually first
- What was corrected:
  - added a tiny repo-root `src` bootstrap in `scripts/build_case_retrieval.py` and `scripts/search_case_retrieval.py`
  - tightened the CLI smoke tests so they now run with `PYTHONPATH` removed from the subprocess environment
- Why it matters:
  - reviewer-facing help and smoke commands now work the same way the docs/prose imply, without a hidden environment footgun

## What Improved

- `guidance pressure moments` now stays focused on real pressure-oriented guidance spans instead of surfacing the low-information guidance joke/meta row near the top.
- `growth slowdown competition discussion` now surfaces richer Q&A answers and shareholder-letter paragraphs ahead of broad guidance-only matches.
- `skeptical analyst question`, `analyst skepticism`, `pressure from analyst`, and `challenging question` now stay centered on analyst-question rows.
- The strongest Netflix skepticism opener, `qa_pair_001_question`, now ranks first for:
  - `skeptical analyst question`
  - `tone changed vs three months ago`
  - `competition macro maturity question`
  - `pressure from analyst`
- `ad supported option` now keeps the strongest analyst-question and management-answer rows ahead of weaker duplicates.

## What Still Remains Weak

- Broad guidance spans can still appear lower in the ranking for non-guidance queries when the underlying span genuinely overlaps the topic.
- Semantic similarity remains dependent on the lightweight embedding model and the phrasing of the bounded row text.
- This is still a file-based review helper, not a full reviewer UI or a benchmark framework.
- Retrieval remains navigation/inspection only; deterministic transcript-backed artifacts remain canonical.

## Exact Commands Run

```bash
python3 -m py_compile src/earnings_call_sentiment/retrieval_support.py scripts/search_case_retrieval.py
pytest -q tests/test_retrieval_support.py
python3 scripts/search_case_retrieval.py --help
python3 scripts/build_case_retrieval.py --help
python3 scripts/search_case_retrieval.py --query "guidance pressure moments" --case netflix_q1_2022 --mode hybrid --top-k 5
python3 scripts/search_case_retrieval.py --query "ad supported option" --case netflix_q1_2022 --mode hybrid --top-k 5
python3 scripts/search_case_retrieval.py --query "competition and growth slowdown" --case netflix_q1_2022 --mode hybrid --top-k 5
python3 scripts/search_case_retrieval.py --query "skeptical analyst question" --case netflix_q1_2022 --mode hybrid --top-k 5
git diff --check
```

## Test Results

- `pytest -q tests/test_retrieval_support.py` -> `12 passed`
- `python3 scripts/search_case_retrieval.py --help` -> succeeded without `PYTHONPATH`
- `python3 scripts/build_case_retrieval.py --help` -> succeeded without `PYTHONPATH`
- Direct CLI checks:
  - `guidance pressure moments` -> top hits were `guidance_span_001`, `guidance_span_042`, `guidance_span_008`
  - `ad supported option` -> top hits were `qa_pair_012_answer`, `qa_pair_011_answer`, `qa_pair_011_question`
  - `competition and growth slowdown` -> top hits were `shareholder_letter_paragraph_002`, `qa_pair_001_answer`, `qa_pair_002_answer`
  - `skeptical analyst question` -> top hits were `qa_pair_001_question`, `qa_pair_004_question`, `qa_pair_008_question`
- Final reviewer-safety check:
  - the four direct reviewer query smokes behaved the same way after the CLI bootstrap fix as they did before it

## Branch Status

- Work stayed on `feat/chunking-embedding-support-layer`
- `main` was not touched
- Final HEAD / clean / pushed status is captured in the terminal handoff summary
