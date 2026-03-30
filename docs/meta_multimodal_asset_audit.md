# Meta Multimodal Asset Audit

- Case: `meta_q3_2022`
- Requested exact MP4 path: `/Users/keith/Desktop/Netflix Meta Nvidia Capstone FINAL SOURCE/Meta/Facebook (META) Q3 2022 Earnings Call.mp4`
- Requested exact MP4 path matched directly: `True`
- Resolved local MP4 fallback used: `not needed`
- Bounded visual analysis usable: `True`

## What Exists

- `transcript_pdf`: `True`
  path: `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-meta-reference-case/data/demo_cases/meta_q3_2022/raw/transcript/meta_q3_2022_earnings_call_transcript.pdf`
- `follow_up_transcript_pdf`: `True`
  path: `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-meta-reference-case/data/demo_cases/meta_q3_2022/raw/follow_up_transcript/meta_q3_2022_follow_up_call_transcript.pdf`
- `results_release_pdf`: `True`
  path: `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-meta-reference-case/data/demo_cases/meta_q3_2022/raw/results_release/meta_q3_2022_results_release.pdf`
- `earnings_presentation_pdf`: `True`
  path: `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-meta-reference-case/data/demo_cases/meta_q3_2022/raw/presentation/meta_q3_2022_earnings_presentation.pdf`
- `video_verification_json`: `True`
  path: `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-meta-reference-case/data/demo_cases/meta_q3_2022/raw/video/video_verification.json`
- `processed_audio_status`: `True`
  path: `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-meta-reference-case/data/demo_cases/meta_q3_2022/processed/audio_behavior/audio_status.json`
- `processed_audio_summary`: `True`
  path: `/Users/keith/Documents/New project/earnings-call-sentiment-from-voice-transcript-with-an-optional-video-24-02-2026-meta-reference-case/data/demo_cases/meta_q3_2022/processed/audio_behavior/audio_behavior_summary.json`

## Missing Or Weak Coverage

- The requested local MP4 lives outside the repo and is not persisted under the case package.
- Only two main-call Q&A windows currently have curated audio timing attached in the repo.
- Follow-up, presentation, and release moments do not carry transcript-aligned main-call video timestamps.

## Conclusion

- The exact requested Meta MP4 path matched directly and was available for a bounded supporting-only visual pass.
- Final persisted visual output was skipped: A bounded visual pass was intentionally skipped after earlier full-video heuristic attempts exceeded the reviewer-safe runtime cap in this session.
