## Branch Cleanup Summary

- Repo path: `/Users/keith/GitHub/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026`
- Branch: `feat/pilot-corpus-and-multimodal-intake`
- Goal: trim generated pilot-corpus bulk so the feature branch keeps pipeline code, manifests, docs, tests, and only tiny representative samples.

### Removed From The Feature Branch

- Bulk committed raw transcript copies for the 20-call pilot set.
- Bulk processed alignment outputs under `data/corpus/processed/alignments/`.
- Bulk processed chunk outputs under `data/corpus/processed/chunks/`.
- Bulk evidence-object exports under `data/corpus/processed/evidence_objects/`.
- Built retrieval index artifacts under `data/corpus/retrieval/pilot_event_index/`.
- Incidental proof artifact drift in `outputs/LLY_2025_Q2_call08/portfolio_proof.json`.

### Intentionally Kept

- Pipeline code in `src/earnings_call_sentiment/`.
- Build and validation scripts in `scripts/`.
- Corpus manifest and schema in `data/corpus/manifests/`.
- Pilot summary in `data/corpus/reports/pilot_corpus_summary.json`.
- Recruiter-facing and reviewer-facing docs in `README.md`, `docs/pilot-corpus.md`, and `pilot_corpus_run_summary.md`.
- Tiny representative samples:
  - `data/corpus/raw/transcripts/GOOGL_2025_Q4_call03.txt`
  - `data/corpus/raw/transcripts/LLY_2025_Q2_call08.txt`
  - `data/corpus/processed/chunks/LLY_2025_Q2_call08.event_chunks.jsonl`
  - `data/corpus/processed/chunks/LLY_2025_Q2_call08.segment_metadata.json`
  - `data/corpus/processed/evidence_objects/LLY_2025_Q2_call08.evidence_objects.jsonl`

### Guardrails Added

- `.gitignore` now ignores regenerated corpus audio, video, bulk transcript copies, processed artifacts, and retrieval index outputs while allowing the committed sample files to stay trackable.
- `scripts/build_pilot_corpus.py` now writes manifest transcript paths back to repo-local source files and only refreshes the explicitly committed sample copies.
- Docs now call out that the full corpus tree and retrieval index are regenerated locally rather than committed.

### Validation

- `git diff --stat main...feat/pilot-corpus-and-multimodal-intake` checked before and after cleanup to confirm the branch was carrying bulk generated outputs that are now removed by this cleanup commit.
- `PYTHONPATH=src python3 -m pytest tests/test_corpus_manifest.py tests/test_corpus_artifacts.py tests/test_retrieval_index.py`
- `PYTHONPATH=src python3 scripts/validate_pilot_corpus.py`
- `make portfolio-ci`

Results:

- `pytest`: passed (`4` tests).
- `validate_pilot_corpus.py`: passed with `20` transcript-verified rows, `7` audio-verified rows, and `0` video-verified rows.
- `make portfolio-ci`: passed.

### Merge Readiness

- Yes, as a merge candidate branch shape. The feature branch keeps the reusable pipeline, manifests, docs, tests, and tiny samples while removing the bulky generated corpus dump and retrieval binaries.
- Remaining reviewer note: the full pilot corpus and retrieval index are intentionally regenerated locally rather than stored in git.

### Screenshot Utility

- Local utility hardened at `~/trash_desktop_screenshots.py`.
- The script now skips iCloud placeholder files, suppresses Finder chatter, times out safely, and prints concise per-file results plus a summary.
- Safe local test used `SCREENSHOT_DESKTOP_DIR` with one normal screenshot file and one simulated iCloud placeholder file; the script trashed the local file, skipped the placeholder, and exited cleanly.
