# Pilot Corpus

## What This Adds
This repo now includes a transcript-first pilot corpus path that is separate from the canonical Eli Lilly portfolio proof bundle.

The pilot path is meant for:
- corpus intake and provenance hardening
- retrieval-ready evidence export
- selective multimodal audit scaffolding
- scaling the workflow from one call to a real batch

It is not a claim that every call already has full local media coverage.

## Current Snapshot
Built on April 23, 2026 from repo-local manifests and committed transcript assets.

Current strict counts:
- pilot cases: `20`
- transcript verified: `20`
- audio verified: `7`
- video verified: `0`

Those numbers come from [`data/corpus/manifests/pilot_corpus_manifest.csv`](../data/corpus/manifests/pilot_corpus_manifest.csv) and are validated by [`scripts/validate_pilot_corpus.py`](../scripts/validate_pilot_corpus.py).

This branch intentionally keeps only tiny representative samples under `data/corpus/`:
- transcript samples: `GOOGL_2025_Q4_call03.txt` and `LLY_2025_Q2_call08.txt`
- processed samples: `LLY_2025_Q2_call08.event_chunks.jsonl`, `LLY_2025_Q2_call08.segment_metadata.json`, and `LLY_2025_Q2_call08.evidence_objects.jsonl`

The full generated corpus tree is meant to be rebuilt locally with the scripts below and is ignored from git on purpose.

## Canonical Layout
```text
data/
  corpus/
    manifests/
      pilot_corpus_manifest.csv
      pilot_corpus_manifest.jsonl
      pilot_corpus_manifest.schema.json
    raw/
      transcripts/
    processed/
      chunks/
      evidence_objects/
      alignments/
    reports/
      pilot_corpus_summary.json
    retrieval/
      pilot_event_index/
```

## Verification Rules
- `transcript_verified=true` means the manifest row resolves to a repo-local transcript source and a recorded provenance trail.
- `audio_verified=true` is only used when the repo already contains committed audio-derived review outputs for that call.
- `video_verified=true` is reserved for calls with a real verified local video or replay artifact path. The current pilot does not claim that yet.
- `transcript_parse_status=timed_segments_available` means the repo already had a processed `transcript.json`.
- `transcript_parse_status=raw_text_only` means the row is still useful for retrieval and manifest coverage, but the call only has transcript text right now.

## Retrieval Artifacts
For each pilot case, the local build path writes:
- `segment_metadata.json`
- `transcript_sectioned.json`
- `qa_pairs.json`
- `event_chunks.jsonl`
- `evidence_objects.jsonl`
- `alignment_windows.json`

These exports preserve:
- case id
- company and fiscal period
- section and speaker role when inferable
- local provenance references
- guidance / uncertainty / pushback flags

## Local Index
The first-pass retrieval baseline is local and cheap by design:
- default provider: deterministic hashing vectors
- optional provider: `sentence_transformers`
- runtime output directory: `data/corpus/retrieval/pilot_event_index/`

This is meant to stand up the retrieval contract and query path before introducing heavier embedding backends.

## Commands
Build:

```bash
PYTHONPATH=src python3 scripts/build_pilot_corpus.py --target-count 20 --embedding-provider hashing
```

Validate:

```bash
PYTHONPATH=src python3 scripts/validate_pilot_corpus.py
```

Focused tests:

```bash
PYTHONPATH=src python3 -m pytest tests/test_corpus_manifest.py tests/test_corpus_artifacts.py tests/test_retrieval_index.py
```

## What Still Needs Work Before 100 Calls
- add more official-source recent large-cap calls so the batch is less dependent on older holdout/watchlist rows
- verify and store real local audio for more non-benchmark calls
- add true video-verified rows rather than replay-page hints
- improve speaker attribution beyond current deterministic heuristics on plain ASR transcripts
- add a stronger embedding backend once the event/evidence contract is stable enough to benchmark
