# Final 16h Ingestion Status

- Companies Scanned: 100
- Calls Scanned: 500
- Extra Nyse Companies Scanned: 0
- Resolved Asset Candidates: 515
- Ranked Asset Candidates: 730
- Permitted Download Rows: 0
- Transcript Asset Candidates Found: 0
- Audio Asset Candidates Found: 0
- Transcript Downloads Attempted: 0
- Transcript Downloads Succeeded: 0
- Audio Downloads Attempted: 0
- Audio Downloads Succeeded: 0
- Registered Transcripts: 0
- Registered Audio Files: 0
- Normalized Transcripts: 0
- Chunks: 0
- Evidence Objects: 0
- Retrieval Objects: 0
- Rag Ready Calls: 0
- Audio Asr Ready Calls: 0

## Top Domains
- data.sec.gov: 500
- www.jpmorganchase.com: 225
- privatebank.jpmorgan.com: 2
- event.webcasts.com: 1
- cloud.impact.jpmchase.com: 1
- www.youtube.com: 1

## Top Blockers
- mismatched_event_period_or_non_earnings: 14
- paywall_or_login_or_drm_blocked: 1
- youtube_media_blocked: 1

## Guardrails
- Raw files committed: false
- Model training run: false
- Embeddings/vector DB committed: false
- Trading/alpha/significance claims: none

## Exact Next Manual Actions
- Review official IR event pages for direct earnings-call transcript/audio links that include exact fiscal period/date.
- Add lawful manual-local transcript/audio files under the Desktop workspace when official direct assets are unavailable.
- Add provider API keys plus license_config_ref before any vendor raw transcript/audio storage.
- Do not use YouTube media unless explicit written authorization is recorded.
