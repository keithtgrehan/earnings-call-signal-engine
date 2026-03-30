# Netflix Multimodal Asset Audit

- Case: `netflix_q1_2022`
- Requested exact MP4 path: `/Users/keith/Desktop/Netflix Meta Nvidia Capstone FINAL SOURCE/Netflix Q1 2022 Earnings Interview.mp4`
- Requested exact MP4 path matched directly: `False`
- Resolved local MP4 fallback found: `/Users/keith/Desktop/Netflix Meta Nvidia Capstone FINAL SOURCE/Netflix/Netflix Q1 2022 Earnings Interview.mp4`
- Bounded visual analysis usable: `True`

## What Exists

- `transcript_pdf`: `True`
  path: `/Users/keith/Documents/New project/main-demo-wt/data/demo_cases/netflix_q1_2022/raw/transcript/netflix_q1_2022_transcript.pdf`
- `shareholder_letter_pdf`: `True`
  path: `/Users/keith/Documents/New project/main-demo-wt/data/demo_cases/netflix_q1_2022/raw/shareholder_letter/netflix_q1_2022_shareholder_letter.pdf`
- `financial_workbook`: `True`
  path: `/Users/keith/Documents/New project/main-demo-wt/data/demo_cases/netflix_q1_2022/raw/financials/netflix_q1_2022_financials.xlsx`
- `income_statement_csv`: `True`
  path: `/Users/keith/Documents/New project/main-demo-wt/data/demo_cases/netflix_q1_2022/raw/financials/netflix_q1_2022_income_statement.csv`
- `video_verification_json`: `True`
  path: `/Users/keith/Documents/New project/main-demo-wt/data/demo_cases/netflix_q1_2022/raw/video/video_verification.json`
- `processed_audio_status`: `True`
  path: `/Users/keith/Documents/New project/main-demo-wt/data/demo_cases/netflix_q1_2022/processed/audio_behavior/audio_status.json`
- `processed_audio_summary`: `True`
  path: `/Users/keith/Documents/New project/main-demo-wt/data/demo_cases/netflix_q1_2022/processed/audio_behavior/audio_behavior_summary.json`

## Missing Or Untracked

- The repo does not track the raw Netflix MP4 in data/demo_cases/netflix_q1_2022/raw/video/.
- The repo does not track the extracted WAV in data/demo_cases/netflix_q1_2022/raw/audio/.

## Conclusion

- The exact requested file path did not match, but a local Netflix MP4 fallback was found and used for a bounded supporting-only visual pass.
