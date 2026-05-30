# Agent Request: Find Audio For First30

## Scope

Find official/direct company-hosted audio or webcast audio URLs for first30 cases that already have clean transcript registration. Audio is support only; transcripts remain canonical.

## Clean Transcript Cases Available Now

- `bac_2025_q4`
- `cat_2024_q4`
- `cat_2025_q1`
- `cat_2025_q2`
- `cat_2025_q3`
- `cat_2025_q4`
- `hd_2024_q1`
- `hd_2024_q2`
- `hd_2024_q3`
- `hd_2024_q4`
- `hd_2025_q4` control fixture
- `jpm_2025_q1`
- `jpm_2025_q2`
- `jpm_2025_q3`
- `jpm_2025_q4`

## Current Audio Status

- `vz_2024_q4` prepared MP3 is registered and ASR-complete, but it is support-only and aligned only to the VZ prepared transcript path from the pair manifest.
- VZ full-call transcript remains blocked by vendor markers; do not use VZ prepared MP3 as full-call Q&A evidence.
- Automated same-domain official-page audio discovery over registered transcript cases found 0 new direct MP3/M4A/WAV URLs.
- No additional audio RAG objects are ready because no other clean direct audio exists.

## Hard Blocks

- No YouTube media without explicit written authorization.
- No vendor raw audio/transcript without `license_config_ref`.
- No paywall/login/DRM/session/signed URL bypass.
- No cloud ASR.

## Required Output

Return candidate rows with `case_id`, `ticker`, `audio_url`, `source_domain`, `source_relation`, `direct_audio`, `review_required`, and `blocked_reason` if any.
