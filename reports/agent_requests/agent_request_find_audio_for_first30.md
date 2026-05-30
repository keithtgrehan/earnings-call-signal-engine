# Agent Request: Find Audio For First30

## Scope

Find official/direct company-hosted audio or webcast audio URLs for first30 cases that already have clean transcript registration. Audio is support only; transcripts remain canonical.

## Clean Transcript Cases Available Now

- `hd_2024_q1`
- `hd_2024_q2`
- `hd_2024_q3`
- `hd_2024_q4`
- `hd_2025_q4` control fixture
- `bac_2025_q4`
- `cat_2025_q4`

## Current Audio Status

- `vz_2024_q4` prepared MP3 is registered, but the full-call transcript is blocked by vendor markers and no ASR is available.
- No audio RAG objects are ready because ASR text plus transcript alignment are missing.

## Hard Blocks

- No YouTube media without explicit written authorization.
- No vendor raw audio/transcript without `license_config_ref`.
- No paywall/login/DRM/session/signed URL bypass.
- No cloud ASR.

## Required Output

Return candidate rows with `case_id`, `ticker`, `audio_url`, `source_domain`, `source_relation`, `direct_audio`, `review_required`, and `blocked_reason` if any.
