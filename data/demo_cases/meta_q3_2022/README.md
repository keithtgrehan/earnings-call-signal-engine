# Meta Q3 2022 Fixed Demo Case

This folder holds a fixed, transcript-first demo package for Meta Q3 2022.

Included raw inputs:
- Q3 2022 earnings call transcript PDF
- Q3 2022 follow-up call transcript PDF
- Q3 2022 results release PDF
- Q3 2022 earnings presentation PDF
- local Q3 2022 video asset for optional supporting audio hooks

Processing boundary:
- the main earnings call transcript is the canonical spoken source
- the follow-up call is additional analyst-pressure context
- the results release and presentation are official disclosure support
- audio/video remain supporting layers only

Key outputs:
- `processed/transcript_text/transcript_cleaned.txt`
- `processed/follow_up_text/follow_up_cleaned.txt`
- `processed/qa_pairs/qa_pairs.json`
- `processed/qa_pairs/follow_up_qa_pairs.json`
- `processed/signals/results_release_evidence.json`
- `processed/signals/presentation_support_metrics.json`
- `processed/signals/financial_context_summary.json`
- `processed/signals/report.md`
- `processed/audio_behavior/audio_status.json`
- `processed/joined_review/joined_qa_audio_review.json`
- `demo/evidence_rows/meta_q3_2022_evidence_rows.json`
- `demo/summary/meta_q3_2022_summary.json`
- `demo/summary/meta_q3_2022_market_context.json`
- `demo/fixtures/meta_q3_2022_fixture.json`

Rebuild from the repo-local raw assets:

```bash
PYTHONPATH=src python3 scripts/build_meta_demo_case.py
```

Notes:
- transcript-first artifacts are the source of truth for this case
- audio timings are attached only to a few curated Q&A moments from the main call
- market reaction context is a historical sanity-check panel, not predictive validation
