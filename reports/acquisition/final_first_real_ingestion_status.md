# Final First Real Ingestion Status

- Companies scanned: 100
- Calls scanned: 500
- Extra NYSE companies scanned beyond first 100: 0
- Manual-local files found: 0
- Transcript asset candidates found: 3
- Audio asset candidates found: 1
- Transcript downloads attempted/succeeded: 3/1
- Audio downloads attempted/succeeded: 1/1
- Registered transcripts: 1
- Registered audio: 1
- Normalized transcripts: 1
- Chunks: 1
- Evidence objects: 1
- Retrieval objects: 1
- Retrieval-object ready calls: 1
- BM25 smoke-ready calls: 1
- evaluated_rag=false
- retrieval_eval_queries_run=0
- retrieval_quality_proven=false
- Audio registered / ASR-ready calls: 1
- ASR transcripts available: 0
- Audio retrieval unavailable until ASR text exists
- Usable transcript/audio pairs: 0

## Top Domains
- data.sec.gov: 500
- www.youtube.com: 275
- www.verizon.com: 230
- investors.att.com: 220
- login.q4inc.com: 205
- d1io3yog0oux5.cloudfront.net: 120
- investors.coca-colacompany.com: 95
- ir.homedepot.com: 80
- event.choruscall.com: 75
- www.bny.com: 50

## Top Blockers
- mismatched_event_period_or_non_earnings: 362
- paywall_or_login_or_drm_blocked: 325
- youtube_media_blocked: 276
- fetch_failed: 172
- signed_or_session_url_blocked: 45
- vendor_raw_requires_license_config_ref: 2

## Exact Next Manual Actions
- Add lawful manual-local transcript/audio files under the Desktop workspace when official direct assets are unavailable.
- Review official IR event pages for exact period/date transcript or replay links.
- Configure provider API keys and license_config_ref before any vendor raw ingestion.
- Do not use YouTube media unless a written authorization reference is present.
