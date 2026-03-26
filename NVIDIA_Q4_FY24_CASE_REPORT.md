# NVIDIA Q4 FY24 Case Report

## What Changed In This Rebuild

- Rebuilt the fixed NVIDIA demo case on branch `feat/demo-case-nvidia-q4-fy2024` using the local transcript PDF at:
  - `data/demo_cases/nvidia_q4_fy2024/raw/transcript/nvidia_q4_fy2024_transcript.pdf`
- Removed the prior transcript provenance issue from the active case package by using the local PDF as the canonical transcript source.
- Kept the correct Seeking Alpha transcript URL as the canonical reference in provenance.
- Kept the old mirror URL only as a fallback reference and did not use it for the rebuilt case.
- Continued to reject the wrong Motley Fool Q4 2023 transcript URL for this case.

## Transcript Provenance

- Canonical case id: `nvidia_q4_fy2024`
- Company / ticker: `NVIDIA` / `NVDA`
- Event date: `2024-02-21`
- Quarter label: `Q4 FY24`
- Fiscal period ended: `2024-01-28`

Primary transcript source now used:
- `data/demo_cases/nvidia_q4_fy2024/raw/transcript/nvidia_q4_fy2024_transcript.pdf`

Reference URLs:
- Official NVIDIA press release:
  - `https://investor.nvidia.com/news/press-release-details/2024/NVIDIA-Announces-Financial-Results-for-Fourth-Quarter-and-Fiscal-2024/`
- Correct transcript reference:
  - `https://seekingalpha.com/article/4672199-nvidia-corporation-nvda-q4-2024-earnings-call-transcript`
- Fallback reference retained only for provenance:
  - `https://invest24.work/transcript/nvda-q4-2024-earnings-call-transcript`
- Explicitly rejected:
  - `https://www.fool.com/earnings/call-transcripts/2023/02/22/nvidia-nvda-q4-2023-earnings-call-transcript/`

Why the prior provenance issue was resolved:
- The active case no longer depends on the earlier fallback transcript snapshot.
- The local PDF text matches the expected Feb. 21, 2024 call opening, participant set, and key Q4 FY24/Q1 FY25 guidance language.
- `quarter_consistency.json` now records:
  - `overall_consistency = "ok"`

## Updated Artifacts

### Builder / provenance

- `scripts/build_nvidia_demo_case.py`
- `data/demo_cases/nvidia_q4_fy2024/source_manifest.json`
- `data/demo_cases/nvidia_q4_fy2024/quarter_consistency.json`

### Transcript-first processed artifacts

- `data/demo_cases/nvidia_q4_fy2024/processed/transcript_text/transcript_raw_extract.txt`
- `data/demo_cases/nvidia_q4_fy2024/processed/transcript_text/transcript_cleaned.txt`
- `data/demo_cases/nvidia_q4_fy2024/processed/transcript_text/transcript_sectioned.json`
- `data/demo_cases/nvidia_q4_fy2024/processed/transcript_text/transcript.json`
- `data/demo_cases/nvidia_q4_fy2024/processed/transcript_text/transcript.txt`
- `data/demo_cases/nvidia_q4_fy2024/processed/qa_pairs/qa_pairs.json`
- `data/demo_cases/nvidia_q4_fy2024/processed/chunks/chunks_scored.csv`
- `data/demo_cases/nvidia_q4_fy2024/processed/chunks/chunks_scored.jsonl`
- `data/demo_cases/nvidia_q4_fy2024/processed/signals/guidance.csv`
- `data/demo_cases/nvidia_q4_fy2024/processed/signals/qa_shift_summary.json`
- `data/demo_cases/nvidia_q4_fy2024/processed/signals/metrics.json`
- `data/demo_cases/nvidia_q4_fy2024/processed/signals/report.md`

### Optional bounded audio support

- `data/demo_cases/nvidia_q4_fy2024/processed/audio_behavior/audio_status.json`
- `data/demo_cases/nvidia_q4_fy2024/processed/audio_behavior/audio_review_rows.json`
- `data/demo_cases/nvidia_q4_fy2024/processed/joined_review/joined_qa_audio_review.json`
- `data/demo_cases/nvidia_q4_fy2024/processed/joined_review/joined_review_moments.json`

### Demo-facing artifacts

- `data/demo_cases/nvidia_q4_fy2024/demo/evidence_rows/nvidia_q4_fy2024_evidence_rows.json`
- `data/demo_cases/nvidia_q4_fy2024/demo/summary/nvidia_q4_fy2024_summary.json`
- `data/demo_cases/nvidia_q4_fy2024/demo/summary/nvidia_q4_fy2024_market_context.json`
- `data/demo_cases/nvidia_q4_fy2024/demo/fixtures/nvidia_q4_fy2024_fixture.json`

## Commands Run

```bash
cp -n '/Users/keith/Downloads/nvidia_earnings_call_transcript.pdf' \
  'data/demo_cases/nvidia_q4_fy2024/raw/transcript/nvidia_q4_fy2024_transcript.pdf'

python -m py_compile scripts/build_nvidia_demo_case.py

PYTHONPATH=src python scripts/build_nvidia_demo_case.py

python - <<'PY'
import json
from pathlib import Path
root = Path('data/demo_cases/nvidia_q4_fy2024')
summary = json.loads((root / 'demo/summary/nvidia_q4_fy2024_summary.json').read_text())
fixture = json.loads((root / 'demo/fixtures/nvidia_q4_fy2024_fixture.json').read_text())
print(summary['quarter_consistency']['overall_consistency'])
print(summary['case_status'])
print(fixture['case_status'])
PY
```

## What Completed Successfully

- The local transcript PDF was detected and used as the canonical transcript source.
- `source_manifest.json` now marks the PDF as primary and keeps the mirror only as reference.
- `quarter_consistency.json` now records:
  - `transcript_source_match = true`
  - `press_release_match = true`
  - `video_match = true`
  - `overall_consistency = "ok"`
- The demo summary and fixture now record:
  - `case_status = "ready"`
- The transcript-first package rebuilt successfully from the local raw assets.
- The rebuilt case now has:
  - `8` evidence rows
  - `3` joined audio review moments

## What Was Skipped Deliberately

- No merge to `main`
- No benchmark / holdout / eval package changes
- No transcript-core logic changes
- No app or UI changes
- No Tesla work

## Remaining Caveats

- The official press release still comes from a saved text snapshot because direct IR requests hit anti-bot protection in this environment.
- The transcript PDF is the canonical local source, but PDF text extraction still contains a few source-level transcription quirks such as minor spelling or formatting noise.
- Audio remains bounded and supporting only. It is not full transcript-to-media alignment.
- The raw transcript PDF, raw MP4, and raw WAV are local assets and are intentionally not committed.

## Ready For Later Local Demo / UI Inclusion?

Yes.

The case is now suitable for later local demo/UI inclusion using the same deterministic-first and normalized artifact contract as the other fixed demo cases.

## Main Branch Status

Nothing from this rebuild was merged into `main`.
