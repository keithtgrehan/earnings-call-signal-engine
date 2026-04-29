# Pilot Corpus Run Summary

## What I Found
- The repo already had enough raw material for a serious pilot corpus: 37 legacy manifest rows, 32 committed raw transcript text files, and 8 processed benchmark-style cases with timed transcript artifacts.
- The biggest gap was not model quality. It was corpus hygiene: no single strict manifest for transcript/audio/video verification, no canonical `data/corpus/` layout, and no reusable export path for sectioned transcripts, Q&A pairs, event chunks, and retrieval-ready evidence objects.
- The current committed media state is honest but incomplete. Transcript coverage is strong, audio-backed review exists for a minority of cases, and video should still be treated as unverified in the strict pilot.

## What Changed
- Added a canonical corpus contract under `data/corpus/` with:
  - `manifests/pilot_corpus_manifest.csv`
  - `manifests/pilot_corpus_manifest.jsonl`
  - `manifests/pilot_corpus_manifest.schema.json`
  - normalized transcript copies under `raw/transcripts/`
  - per-case chunk, evidence, and alignment exports under `processed/`
  - a local retrieval baseline under `retrieval/pilot_event_index/`
- Added manifest/schema and export code:
  - `src/earnings_call_sentiment/corpus.py`
  - `src/earnings_call_sentiment/corpus_artifacts.py`
  - `src/earnings_call_sentiment/retrieval_index.py`
- Added orchestration and validation scripts:
  - `scripts/build_pilot_corpus.py`
  - `scripts/validate_pilot_corpus.py`
- Added focused tests for the new contract and retrieval baseline.
- Updated the README and added `docs/pilot-corpus.md` so the new path is legible to the next reviewer.

## Scripts Added Or Edited
- Added `scripts/build_pilot_corpus.py`
- Added `scripts/validate_pilot_corpus.py`
- README updated with pilot corpus commands and verification counts
- Added `docs/pilot-corpus.md`

## Schema Changes
- Introduced one strict pilot manifest schema with explicit fields for:
  - transcript/audio/video URLs
  - transcript/audio/video local paths
  - transcript/audio/video verified flags
  - source types
  - parse/fetch statuses
  - provenance JSON
- Added deterministic validation for:
  - required fields
  - allowed status enums
  - local path existence
  - provenance JSON integrity

## Pilot Corpus Coverage
- Calls sourced into the current pilot: `20`
- Transcript verified: `20`
- Audio verified: `7`
- Video verified: `0`

Current pilot cases:
- `NVDA_2026_Q4_call07`
- `GOOGL_2025_Q4_call03`
- `PLTR_2025_Q4_call01`
- `AAPL_2026_Q1_call06`
- `MSFT_2026_Q2_call05`
- `LLY_2025_Q2_call08`
- `LEU_2025_Q4_call02`
- `IBM_2025_Q4_call04`
- `LMND_2025_Q4_watchhold04`
- `AMZN_2025_Q4_watchhold01`
- `BE_2025_Q4_watchhold05`
- `ETN_2025_Q4_watchhold02`
- `NVDA_2026_Q3_holdout03`
- `GOOGL_2025_Q3_holdout02`
- `MSFT_2026_Q1_holdout04`
- `IBM_2025_Q3_holdout01`
- `VRT_2025_Q3_watchhold03`
- `EVER_2025_Q2_holdout07`
- `BE_2025_Q2_watchhold06`
- `NBIS_2025_Q2_watchhold07`

## What Improved For Technical Credibility
- Retrieval objects now preserve case ids, fiscal period, section, speaker role, and local provenance references instead of relying only on transcript sprawl.
- Processed cases now export a reusable evidence layer with:
  - `segment_metadata.json`
  - `transcript_sectioned.json`
  - `qa_pairs.json`
  - `event_chunks.jsonl`
  - `evidence_objects.jsonl`
  - `alignment_windows.json`
- A cheap local retrieval baseline now exists and can be queried without paid APIs.
- The pilot manifest is explicit about what is truly verified and what is still transcript-only.

## What Improved For Recruiter / Reviewer Readability
- The repo now has one obvious pilot-corpus story in addition to the canonical LLY proof bundle.
- The README and pilot doc explain the transcript-first boundary clearly:
  - transcript outputs are source of truth
  - audio is selective support
  - video is not over-claimed
- The current corpus counts and limitations are visible in-repo instead of living in ad hoc notes.

## Preserved But Not Fully Merged
- Existing benchmark, holdout, watchlist, and historical manifests were preserved as inputs.
- The pilot builder curates from those sources into one strict manifest instead of rewriting or deleting the legacy packages.
- The current pilot intentionally leaves many audio/video source fields blank when the repo does not yet contain a verifiable local media artifact.

## Known Limitations Remaining
- `video_verified` remains `0`, which is the honest state of the strict pilot.
- Only `7` cases have committed audio-derived review outputs today.
- Speaker attribution on plain ASR transcripts is still heuristic.
- The 20-call set is stronger than before, but it still leans on holdout/watchhold transcript rows because the repo does not yet contain a broader recent large-cap official replay pack.
- The local retrieval baseline currently uses deterministic hashing vectors by default. It is useful for the retrieval contract, but not yet a benchmark-quality embedding setup.

## Validation Commands Run
```bash
PYTHONPATH=src python3 -m pytest tests/test_corpus_manifest.py tests/test_corpus_artifacts.py tests/test_retrieval_index.py
PYTHONPATH=src python3 scripts/build_pilot_corpus.py --target-count 20 --embedding-provider hashing
PYTHONPATH=src python3 scripts/validate_pilot_corpus.py
PYTHONPATH=src python3 - <<'PY'
from pathlib import Path
from earnings_call_sentiment.retrieval_index import query_retrieval_index
print(query_retrieval_index(output_dir=Path('data/corpus/retrieval/pilot_event_index'), query='revenue guidance and outlook', top_k=3))
PY
make portfolio-ci
```

## Git Status At Write Time
- Branch: `feat/pilot-corpus-and-multimodal-intake`
- Feature commit: `3d690c9` (`feat: add pilot corpus intake and retrieval baseline`)
- Push status at write time: pending final branch push
