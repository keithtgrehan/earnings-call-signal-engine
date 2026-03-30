# Chunking + Embedding Summary

## What Was Built

- Added `src/earnings_call_sentiment/retrieval_support.py`
  - bounded retrieval row normalization
  - optional embedding export
  - hybrid lexical / semantic search helpers
- Added CLI scripts:
  - `scripts/build_case_retrieval.py`
  - `scripts/search_case_retrieval.py`
- Built reviewable retrieval bundles for:
  - `netflix_q1_2022`
  - `nvidia_q4_fy2024`
- Added focused tests in `tests/test_retrieval_support.py`
- Added audit, design, demo, and PR handoff docs

## What Remains Canonical

- transcript-backed chunks
- deterministic guidance / QA / review artifacts
- explicit source locators and bounded spans

The retrieval bundle is supporting-only. It does not replace the deterministic case pack.

## What Retrieval Now Supports

- lexical search over bounded case rows
- optional semantic similarity over the same rows
- hybrid ranking when embeddings are available
- row-seeded similarity search using an existing `row_id`
- provenance-preserving output for:
  - transcript chunks
  - analyst question spans
  - Q&A answer spans
  - guidance spans
  - shareholder-letter paragraphs for Netflix
  - press-release paragraphs for NVIDIA

## Exact Commands Run

Build bundles:

```bash
PYTHONPATH=src python3 scripts/build_case_retrieval.py --case-id netflix_q1_2022 --no-embeddings
PYTHONPATH=src python3 scripts/build_case_retrieval.py --case-id netflix_q1_2022 --model-name sentence-transformers/all-MiniLM-L6-v2 --device cpu
PYTHONPATH=src python3 scripts/build_case_retrieval.py --case-id nvidia_q4_fy2024 --model-name sentence-transformers/all-MiniLM-L6-v2 --device cpu
```

Demo searches:

```bash
PYTHONPATH=src python3 scripts/search_case_retrieval.py "guidance pressure moments" --case-id netflix_q1_2022 --mode hybrid --top-k 6
PYTHONPATH=src python3 scripts/search_case_retrieval.py "growth slowdown competition discussion" --case-id netflix_q1_2022 --mode hybrid --top-k 6
PYTHONPATH=src python3 scripts/search_case_retrieval.py "ad-supported strategy moments" --case-id netflix_q1_2022 --mode hybrid --top-k 6
PYTHONPATH=src python3 scripts/search_case_retrieval.py --case-id netflix_q1_2022 --mode hybrid --top-k 6 --like-row-id qa_pair_011_question
```

Tests:

```bash
PYTHONPATH=src pytest -q tests/test_retrieval_support.py
PYTHONPATH=src pytest -q tests/test_demo_case_loader.py tests/test_demo_case_payloads.py tests/test_review_workflow.py tests/test_review_app.py
```

## Models Actually Used

- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- Runtime stack: existing `transformers` + `torch`

No vector database was introduced.

## What Was Skipped

- no vector DB or ANN service
- no UI wiring beyond the reusable bundle + CLI layer
- no broad repo-wide wording rewrite
- curated multimodal rows were left opt-in rather than included by default in the shipped bundles

## Limitations

- bundle quality depends on the quality of the existing deterministic artifact boundaries
- some guidance rows are broad because the underlying guidance extractor is intentionally inclusive
- semantic similarity is only as good as the bounded row text and lightweight embedding model
- NVIDIA uses press-release paragraphs instead of shareholder-letter paragraphs because that is the existing case artifact

## Recommended Next Step

Use the new row schema in the review shell or demo UI as a supporting-only retrieval panel:

- search by free text
- click through to the canonical source artifact
- show the exact source locator and transcript-backed span beside every result
