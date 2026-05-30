# Final Next Ingestion Status

- Companies scanned: 100
- Calls scanned: 500
- Matched-pair candidate rows: 2
- First-30 transcript target rows: 30
- First-30 control fixture rows: 1
- VZ 2024 Q4 matched-pair status: approval-gated candidate
- HD 2025 Q4 control fixture status: registered transcript, 21 chunk rows, 21 retrieval objects
- Transcript downloads attempted/succeeded: 3/1
- Audio downloads attempted/succeeded: 1/1
- Registered transcripts/audio: 1/1
- Usable transcript/audio pairs: 0
- ASR transcripts available: 0
- Retrieval eval queries run: 5
- Retrieval status: smoke metrics only; `evaluated_rag=false`
- Raw transcript/audio/chunk/ASR text committed: false

## Remaining Blockers
- VZ transcript and direct MP3 still need source-terms review before matched-pair promotion.
- HD audio remains metadata-only because the ChorusCall URL is a player, not a direct audio asset.
- Local ASR dependency is unavailable, so audio retrieval objects are not exportable.
- First-30 transcript rows are approval-gated; raw downloads stay Desktop-only after promotion.
