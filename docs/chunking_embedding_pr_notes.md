# PR Notes: Chunking + Embedding Support Layer

## Summary

This change adds a bounded, file-based retrieval sidecar on top of the existing transcript-first case packs.

It does **not** replace deterministic outputs.

## Reviewer Guide

Start here:

- `docs/chunking_embedding_audit.md`
- `docs/chunking_embedding_design.md`
- `docs/netflix_retrieval_demo.md`
- `src/earnings_call_sentiment/retrieval_support.py`
- `tests/test_retrieval_support.py`

Then inspect generated artifacts:

- `data/demo_cases/netflix_q1_2022/demo/retrieval/netflix_retrieval_manifest.json`
- `data/demo_cases/netflix_q1_2022/demo/retrieval/netflix_retrieval_rows.jsonl`
- `data/demo_cases/nvidia_q4_fy2024/demo/retrieval/nvidia_retrieval_manifest.json`

## Key Points

- chunking remains canonical
- retrieval rows are derived from deterministic case artifacts only
- every result keeps `source_artifact` and `source_locator`
- lexical retrieval works without embeddings
- semantic retrieval uses a lightweight local embedding model
- row-to-row similarity is supported through `--like-row-id`

## Main Files

- `src/earnings_call_sentiment/retrieval_support.py`
- `scripts/build_case_retrieval.py`
- `scripts/search_case_retrieval.py`
- `tests/test_retrieval_support.py`

## Outputs Added

Netflix:

- `data/demo_cases/netflix_q1_2022/demo/retrieval/netflix_retrieval_rows.jsonl`
- `data/demo_cases/netflix_q1_2022/demo/retrieval/netflix_retrieval_manifest.json`
- `data/demo_cases/netflix_q1_2022/demo/retrieval/netflix_retrieval_embeddings.npy`

NVIDIA:

- `data/demo_cases/nvidia_q4_fy2024/demo/retrieval/nvidia_retrieval_rows.jsonl`
- `data/demo_cases/nvidia_q4_fy2024/demo/retrieval/nvidia_retrieval_manifest.json`
- `data/demo_cases/nvidia_q4_fy2024/demo/retrieval/nvidia_retrieval_embeddings.npy`

## Risk / Limitation Notes

- guidance retrieval inherits the breadth of the current deterministic guidance extractor
- semantic matches are navigation cues, not evidence adjudication
- management-document artifacts differ by case:
  - Netflix uses shareholder-letter paragraphs
  - NVIDIA uses press-release paragraphs
