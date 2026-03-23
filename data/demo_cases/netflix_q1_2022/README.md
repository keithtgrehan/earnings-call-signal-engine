# Netflix Q1 2022 Fixed Demo Case

This folder is a fixed, transcript-first demo package built from the uploaded Netflix Q1 2022 materials.

What is included:
- Q1 2022 earnings interview transcript PDF
- Q1 2022 shareholder letter PDF
- Q1 2022 financial workbook and income statement CSV
- transcript-first processed artifacts for review
- demo-ready JSON fixtures for later UI work

Quarter-consistency result:
- the transcript PDF is Q1 2022
- the file named `Netflix-transcript Q2 2022` was a mislabeled duplicate of the Q1 transcript
- the shareholder letter and financial files match Q1 2022
- the uploaded video is a real Q2 2022 earnings interview and was intentionally excluded from the Q1 demo package

Transcript-first boundary:
- transcript-backed processed artifacts are the source of truth for this case
- audio/video remain supporting layers only
- because the uploaded video was quarter-mismatched, audio hooks were skipped and the package records that status explicitly

Key artifacts:
- `processed/joined_review/quarter_consistency.json`
- `processed/transcript_text/transcript_cleaned.txt`
- `processed/qa_pairs/qa_pairs.json`
- `processed/signals/report.md`
- `processed/signals/guidance.csv`
- `processed/signals/shareholder_letter_evidence.json`
- `processed/signals/financial_context_summary.json`
- `processed/audio_behavior/audio_status.json`
- `demo/evidence_rows/netflix_demo_evidence_rows.json`
- `demo/summary/netflix_demo_summary.json`
- `demo/fixtures/netflix_demo_fixture.json`

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
- synthetic transcript timing is used only to keep the deterministic review pipeline runnable without quarter-consistent media
- this package is for evidence-backed review support, not predictive validation or trading claims
