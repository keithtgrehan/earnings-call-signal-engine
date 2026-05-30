# Agent Request: Find Audio For First30

## Scope

Find official/direct company-hosted audio or webcast audio URLs for first30 cases that already have clean transcript registration. Audio is support only; transcripts remain canonical.

## Clean Transcript Cases Available Now

- `bac_2025_q4`
- `cat_2024_q4`, `cat_2025_q1`, `cat_2025_q2`, `cat_2025_q3`, `cat_2025_q4`
- `f_2025_q1`, `f_2025_q2`, `f_2025_q3`, `f_2025_q4`
- `hd_2024_q1`, `hd_2024_q2`, `hd_2024_q3`, `hd_2024_q4`, `hd_2025_q4`
- `jpm_2024_q1`, `jpm_2024_q2`, `jpm_2024_q3`, `jpm_2024_q4`
- `jpm_2025_q1`, `jpm_2025_q2`, `jpm_2025_q3`, `jpm_2025_q4`
- `lyb_2025_q1`, `lyb_2025_q2`, `lyb_2025_q3`, `lyb_2025_q4`
- `rddt_2025_q2`, `rddt_2025_q3`, `rddt_2025_q4`
- `uber_2025_q4` prepared remarks only; do not treat as full-call Q&A transcript without a clean full-call source.

## Current Audio Status

- Registered audio remains 1: `vz_2024_q4` prepared MP3.
- VZ ASR is complete with 249 segment rows.
- VZ alignment is partial, prepared-only, and review-required.
- Automated official-page audio discovery found 0 new direct downloadable MP3/M4A/WAV URLs.
- Webcast/player-only metadata was preserved where found; no player pages were downloaded, submitted, or scraped for signed media.
- No additional audio RAG objects are ready because no other clean direct audio exists.

## Hard Blocks

- No YouTube media without explicit written authorization.
- No vendor raw audio/transcript without `license_config_ref`.
- No paywall/login/DRM/session/signed URL bypass.
- No cloud ASR.

## Required Output

Return candidate rows with `case_id`, `ticker`, `audio_url`, `source_domain`, `source_relation`, `direct_audio`, `review_required`, and `blocked_reason` if any.
