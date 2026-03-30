# Netflix Q1 2022 Fixed Demo Case

This folder is a fixed, transcript-first demo package built from the uploaded Netflix Q1 2022 materials.

What is included:
- Q1 2022 earnings interview transcript PDF
- Q1 2022 shareholder letter PDF
- Q1 2022 financial workbook and income statement CSV
- transcript-first processed artifacts for review
- verified Q1 2022 video stored locally for optional supporting audio hooks
- extracted mono 16 kHz WAV audio generated from the verified Q1 video when available
- demo-ready JSON fixtures for later UI work
- supporting-only retrieval bundle for lexical / semantic navigation over bounded case rows

Quarter-consistency result:
- the transcript PDF is Q1 2022
- the file named `Netflix-transcript Q2 2022` was a mislabeled duplicate of the Q1 transcript
- the shareholder letter and financial files match Q1 2022
- the active local video asset now verifies as Q1 2022 and is treated as optional supporting media for this case

Transcript-first boundary:
- transcript-backed processed artifacts are the source of truth for this case
- audio/video remain supporting layers only
- audio timings are only attached to a few curated Q&A moments matched against an ASR transcript
- the package records audio/media status explicitly instead of pretending there is full transcript-to-video alignment

Key artifacts:
- `processed/joined_review/quarter_consistency.json`
- `processed/transcript_text/transcript_cleaned.txt`
- `processed/qa_pairs/qa_pairs.json`
- `processed/signals/report.md`
- `processed/signals/guidance.csv`
- `processed/signals/shareholder_letter_evidence.json`
- `processed/signals/financial_context_summary.json`
- `processed/audio_behavior/audio_status.json`
- `processed/audio_behavior/audio_behavior_summary.json`
- `processed/audio_behavior/audio_review_rows.json`
- `processed/joined_review/joined_qa_audio_review.json`
- `demo/evidence_rows/netflix_demo_evidence_rows.json`
- `demo/evidence_rows/netflix_q1_2022_evidence_rows.json`
- `demo/summary/netflix_demo_summary.json`
- `demo/summary/netflix_q1_2022_summary.json`
- `demo/summary/netflix_q1_2022_market_context.json`
- `demo/retrieval/netflix_retrieval_rows.jsonl`
- `demo/retrieval/netflix_retrieval_manifest.json`
- `demo/retrieval/netflix_retrieval_embeddings.npy`
- `demo/retrieval/README.md`
- `demo/fixtures/netflix_demo_fixture.json`
- `demo/fixtures/netflix_q1_2022_fixture.json`

Rebuild from the original uploaded asset folder:

```bash
PYTHONPATH=src python3 scripts/build_netflix_demo_case.py \
  --source-dir "/path/to/netflix-uploaded-assets"
```

Rebuild from the repo-local copied raw assets only:

```bash
PYTHONPATH=src python3 scripts/build_netflix_demo_case.py
```

Limitations:
- transcript-first chunks still use synthetic timing to keep the deterministic review pipeline runnable
- optional audio support is limited to a few curated Q&A moments matched against an ASR transcript
- retrieval is a supporting-only navigation layer over bounded deterministic artifacts
- this package is for evidence-backed review support, not predictive validation or trading claims
