# NVIDIA Q4 FY24 Case Report

## What Was Added

- New branch-only NVIDIA demo-case builder:
  - `scripts/build_nvidia_demo_case.py`
- New fixed case package rooted at:
  - `data/demo_cases/nvidia_q4_fy2024/`
- New provenance and consistency artifacts:
  - `data/demo_cases/nvidia_q4_fy2024/source_manifest.json`
  - `data/demo_cases/nvidia_q4_fy2024/quarter_consistency.json`
- New transcript-first processed artifacts, demo evidence rows, summary, fixture, and optional bounded audio support for the correct NVIDIA Q4 FY24 call.

## Exact Files Created

### Code / docs

- `scripts/build_nvidia_demo_case.py`
- `data/demo_cases/nvidia_q4_fy2024/README.md`

### Case root

- `data/demo_cases/nvidia_q4_fy2024/source_manifest.json`
- `data/demo_cases/nvidia_q4_fy2024/quarter_consistency.json`

### Raw assets

- `data/demo_cases/nvidia_q4_fy2024/raw/transcript/nvidia_q4_fy2024_transcript.html`
- `data/demo_cases/nvidia_q4_fy2024/raw/transcript/nvidia_q4_fy2024_transcript.txt`
- `data/demo_cases/nvidia_q4_fy2024/raw/shareholder_letter/nvidia_q4_fy2024_press_release.md`
- `data/demo_cases/nvidia_q4_fy2024/raw/shareholder_letter/nvidia_q4_fy2024_press_release.txt`
- `data/demo_cases/nvidia_q4_fy2024/raw/financials/nvidia_q4_fy2024_key_metrics.csv`
- `data/demo_cases/nvidia_q4_fy2024/raw/video/nvidia_q4_fy2024_video.mp4`
- `data/demo_cases/nvidia_q4_fy2024/raw/video/video_verification.json`
- `data/demo_cases/nvidia_q4_fy2024/raw/audio/nvidia_q4_fy2024_audio.wav`

### Processed transcript / chunks / qa / signals

- `data/demo_cases/nvidia_q4_fy2024/processed/transcript_text/transcript_raw_extract.txt`
- `data/demo_cases/nvidia_q4_fy2024/processed/transcript_text/transcript_cleaned.txt`
- `data/demo_cases/nvidia_q4_fy2024/processed/transcript_text/transcript_sectioned.json`
- `data/demo_cases/nvidia_q4_fy2024/processed/transcript_text/transcript.json`
- `data/demo_cases/nvidia_q4_fy2024/processed/transcript_text/transcript.txt`
- `data/demo_cases/nvidia_q4_fy2024/processed/transcript_text/press_release_text.txt`
- `data/demo_cases/nvidia_q4_fy2024/processed/chunks/segment_metadata.json`
- `data/demo_cases/nvidia_q4_fy2024/processed/chunks/chunks_scored.csv`
- `data/demo_cases/nvidia_q4_fy2024/processed/chunks/chunks_scored.jsonl`
- `data/demo_cases/nvidia_q4_fy2024/processed/qa_pairs/qa_pairs.json`
- `data/demo_cases/nvidia_q4_fy2024/processed/signals/press_release_evidence.json`
- `data/demo_cases/nvidia_q4_fy2024/processed/signals/financial_context_summary.json`
- `data/demo_cases/nvidia_q4_fy2024/processed/signals/sentiment_segments.csv`
- `data/demo_cases/nvidia_q4_fy2024/processed/signals/guidance.csv`
- `data/demo_cases/nvidia_q4_fy2024/processed/signals/guidance_revision.csv`
- `data/demo_cases/nvidia_q4_fy2024/processed/signals/tone_changes.csv`
- `data/demo_cases/nvidia_q4_fy2024/processed/signals/behavioral_summary.json`
- `data/demo_cases/nvidia_q4_fy2024/processed/signals/qa_shift_segments.csv`
- `data/demo_cases/nvidia_q4_fy2024/processed/signals/qa_shift_summary.json`
- `data/demo_cases/nvidia_q4_fy2024/processed/signals/analyst_skepticism.csv`
- `data/demo_cases/nvidia_q4_fy2024/processed/signals/reassurance_signals.csv`
- `data/demo_cases/nvidia_q4_fy2024/processed/signals/uncertainty_signals.csv`
- `data/demo_cases/nvidia_q4_fy2024/processed/signals/risk_metrics.json`
- `data/demo_cases/nvidia_q4_fy2024/processed/signals/metrics.json`
- `data/demo_cases/nvidia_q4_fy2024/processed/signals/report.md`
- `data/demo_cases/nvidia_q4_fy2024/processed/signals/sentiment_timeline.png`

### Audio / joined review

- `data/demo_cases/nvidia_q4_fy2024/processed/audio_behavior/audio_extraction_status.json`
- `data/demo_cases/nvidia_q4_fy2024/processed/audio_behavior/audio_transcript_segments.json`
- `data/demo_cases/nvidia_q4_fy2024/processed/audio_behavior/audio_aligned_qa_segments.csv`
- `data/demo_cases/nvidia_q4_fy2024/processed/audio_behavior/audio_behavior_segments.csv`
- `data/demo_cases/nvidia_q4_fy2024/processed/audio_behavior/audio_behavior_summary.json`
- `data/demo_cases/nvidia_q4_fy2024/processed/audio_behavior/audio_review_rows.json`
- `data/demo_cases/nvidia_q4_fy2024/processed/audio_behavior/audio_status.json`
- `data/demo_cases/nvidia_q4_fy2024/processed/joined_review/joined_qa_audio_review.json`
- `data/demo_cases/nvidia_q4_fy2024/processed/joined_review/joined_review_moments.json`
- `data/demo_cases/nvidia_q4_fy2024/processed/joined_review/quarter_consistency.json`

### Demo-facing artifacts

- `data/demo_cases/nvidia_q4_fy2024/demo/evidence_rows/nvidia_q4_fy2024_evidence_rows.json`
- `data/demo_cases/nvidia_q4_fy2024/demo/evidence_rows/nvidia_demo_evidence_rows.json`
- `data/demo_cases/nvidia_q4_fy2024/demo/summary/nvidia_q4_fy2024_market_context.json`
- `data/demo_cases/nvidia_q4_fy2024/demo/summary/nvidia_q4_fy2024_summary.json`
- `data/demo_cases/nvidia_q4_fy2024/demo/summary/nvidia_demo_summary.json`
- `data/demo_cases/nvidia_q4_fy2024/demo/fixtures/nvidia_q4_fy2024_fixture.json`
- `data/demo_cases/nvidia_q4_fy2024/demo/fixtures/nvidia_demo_fixture.json`

## Commands Run

### Inspection / branch setup

```bash
pwd
git branch --show-current
git status --short
find data/demo_cases -maxdepth 3 -type d | sort
sed -n '1,260p' scripts/build_netflix_demo_case.py
sed -n '1,260p' scripts/build_meta_demo_case.py
sed -n '1,260p' src/earnings_call_sentiment/demo_case_payloads.py
git checkout -b feat/demo-case-nvidia-q4-fy2024
```

### Source and media checks

```bash
ffprobe -v error -show_entries format=duration:stream=codec_type -of json '/Users/keith/Downloads/YTDown.com_YouTube_Listen-Nvidia-delivers-Q4-FY24-earnings-_Media_txOv_pi-_R4_002_720p.mp4'
python3 - <<'PY'
import requests
print(requests.get('https://investor.nvidia.com/news/press-release-details/2024/NVIDIA-Announces-Financial-Results-for-Fourth-Quarter-and-Fiscal-2024/', timeout=30, headers={'User-Agent':'Mozilla/5.0'}).status_code)
print(requests.get('https://seekingalpha.com/article/4672199-nvidia-corporation-nvda-q4-2024-earnings-call-transcript', timeout=30, headers={'User-Agent':'Mozilla/5.0'}).status_code)
PY
python3 - <<'PY'
import requests,re
text=requests.get('https://invest24.work/transcript/nvda-q4-2024-earnings-call-transcript', timeout=30, headers={'User-Agent':'Mozilla/5.0'}).text
for pattern in [r'NVIDIA.*Q4 2024 Earnings Call Transcript', r'Feb(?:ruary)? 21, 2024', r'Jensen Huang', r'Colette Kress', r'Operator']:
    print(pattern, bool(re.search(pattern, text, re.I)))
PY
```

### Build / rebuild

```bash
python3 -m py_compile scripts/build_nvidia_demo_case.py
PYTHONPATH=src python3 scripts/build_nvidia_demo_case.py --video-path '/Users/keith/Downloads/YTDown.com_YouTube_Listen-Nvidia-delivers-Q4-FY24-earnings-_Media_txOv_pi-_R4_002_720p.mp4'
PYTHONPATH=src python3 scripts/build_nvidia_demo_case.py
```

### Validation

```bash
python3 - <<'PY'
import json
from pathlib import Path
root=Path('data/demo_cases/nvidia_q4_fy2024')
summary=json.loads((root/'demo/summary/nvidia_q4_fy2024_summary.json').read_text())
fixture=json.loads((root/'demo/fixtures/nvidia_q4_fy2024_fixture.json').read_text())
evidence=json.loads((root/'demo/evidence_rows/nvidia_q4_fy2024_evidence_rows.json').read_text())
joined=json.loads((root/'processed/joined_review/joined_qa_audio_review.json').read_text())
print({
  'evidence_rows': len(evidence['rows']),
  'joined_audio_rows': len(joined['rows']),
  'case_status': fixture['case_status'],
  'overall_consistency': summary['quarter_consistency']['overall_consistency'],
})
PY
git --no-pager diff --check
rg -n --color never '/Users/keith|/mnt/data' data/demo_cases/nvidia_q4_fy2024 scripts/build_nvidia_demo_case.py
```

## What Completed Successfully

- Created the canonical case root `data/demo_cases/nvidia_q4_fy2024/`.
- Copied the verified local MP4 into `raw/video/nvidia_q4_fy2024_video.mp4`.
- Saved the official NVIDIA press release as a local raw snapshot.
- Saved the correct-quarter transcript locally and explicitly pinned the Seeking Alpha URL as the canonical reference.
- Wrote `source_manifest.json` and `quarter_consistency.json`.
- Built transcript-first processed artifacts:
  - cleaned transcript
  - transcript segments
  - `chunks_scored.csv`
  - `qa_pairs.json`
  - deterministic signal/report outputs
- Built demo-facing artifacts:
  - normalized evidence rows
  - normalized fixture
  - normalized summary
  - market-context panel
- Extracted mono 16 kHz WAV audio from the local video.
- Generated bounded supporting audio artifacts and 2 joined Q&A/audio moments.
- Verified the case rebuilds from repo-local raw assets without requiring the external local Downloads path.

## What Failed

- Direct HTTP fetches of the official NVIDIA IR page and the canonical Seeking Alpha transcript page both hit anti-bot protection in this environment.
- Because of that, the local saved transcript content came from an accessible mirror, not a direct Seeking Alpha download.

## What Was Skipped Deliberately

- No changes to `main`.
- No benchmark / holdout / eval package changes.
- No transcript-core logic changes.
- No app or UI changes.
- No visual / bounded-video behavior beyond audio extraction and audio-backed Q&A review moments.
- No attempt to pull the wrong Motley Fool Q4 2023 transcript.

## Ready For Later Demo / UI Inclusion?

Yes, with one explicit caution:

- `quarter_consistency.json` is intentionally `warn`, not `pass`, because the canonical Seeking Alpha transcript URL could not be fetched directly in this environment and the saved transcript content came from an accessible mirror after title/date/participant verification.

Operationally, the package is still ready for later inclusion in demo/UI work:

- deterministic-first artifacts are present
- evidence rows are non-empty
- fixture and summary files exist
- optional bounded audio support exists

## Remaining Manual Tasks

- If you want first-party transcript provenance stronger than the current `warn` state, save a direct local snapshot of the Seeking Alpha transcript page or another approved first-party licensed transcript copy for this same Feb. 21, 2024 call.
- If you later want richer financial context than the press-release tables, add a separate raw financial statement source for this case.

## Main Branch Status

Nothing in this task was merged into `main`.
