# User-Authorized Ingest Summary

- Companies processed: 100
- Calls processed: 500
- Permitted download rows: 1000
- Transcript downloads attempted: 500
- Transcript downloads succeeded: 0
- Audio downloads attempted: 500
- Audio downloads succeeded: 0
- Registered transcripts: 0
- Registered audio: 0
- Transcript chunks: 0
- Audio RAG records: 0
- Agent 1 status: NOT_READY
- Training readiness: NOT_READY

## Blocked Reasons

- `not_direct_transcript_url`: 470
- `not_direct_audio_url`: 500
- `content_not_transcript_like`: 20
- `download_failed:The read operation timed out`: 5
- `download_failed:HTTP Error 404: Not Found`: 5

## Next Manual Actions

- Replace IR landing-page placeholders with exact transcript or direct audio URLs for approved sources.
- Keep raw transcript/audio files under the Desktop workspace only.
- Add license_config_ref before any vendor raw use.
- Add youtube_written_authorization_ref before any YouTube media use.
