# Audio Status

The expected Q1 audio target for this fixed demo case is:

- `netflix_q1_2022_audio.wav`

When the verified Q1 video is present at `../video/netflix_q1_2022_video.mp4`, the builder extracts this file automatically as mono 16 kHz WAV audio.

The raw WAV is a local working asset rather than a required tracked artifact. Transcript-first processed artifacts remain the source of truth even when the supporting audio layer is available.

See:
- `../video/video_verification.json`
- `../../processed/audio_behavior/audio_status.json`
- `../../processed/audio_behavior/audio_extraction_status.json`
