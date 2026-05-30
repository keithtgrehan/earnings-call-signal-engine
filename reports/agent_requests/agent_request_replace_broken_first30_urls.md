# Agent Request: Replace Broken First30 Transcript URLs

## Scope

Find official/direct company-hosted transcript URLs for the unresolved NYSE first30 cases. Raw PDFs/text must remain Desktop-only. Do not use vendor transcript pages, paywalled/login sources, YouTube media, or signed/session URLs.

## Current Blockers

- `vz_2024_q4`: Verizon full-call PDF is company-hosted but contains Refinitiv StreetEvents vendor markers; blocked without `license_config_ref`.
- `crm_2025_q4`: Q4CDN PDF contains vendor copyright markers; blocked without `license_config_ref`.
- Remaining first30 Q4 rows for `DOW`, `EQT`, `F`, `HIG`, `LYB`, `OC`, `OMC`, `RDDT`, `RF`, `UBER`, and `VZ` 2025 quarters need direct official transcript URLs or safe replacements.

## Already Resolved

- `hd_2024_q1`, `hd_2024_q2`, `hd_2024_q3`, and `hd_2024_q4` were replaced with official Home Depot IR document URLs in the generated ingestion manifest.
- `bac_2025_q4` and `cat_2025_q4` parsed and registered from official IR CDN URLs.
- `jpm_2025_q1`, `jpm_2025_q2`, `jpm_2025_q3`, and `jpm_2025_q4` are resolved to direct official JPMC PDFs, downloaded Desktop-only, parsed, and registered by path/hash only.
- `cat_2024_q4`, `cat_2025_q1`, `cat_2025_q2`, `cat_2025_q3`, and `cat_2025_q4` are resolved to clean Caterpillar official IR CDN PDFs, downloaded Desktop-only, parsed, and registered by path/hash only with `rights_review_required=true`.

## Current Corpus Count

- Registered first30/control transcripts: 15
- Normalized transcripts: 15
- Download-allowed rows: 14
- Remaining direct-transcript URL blockers: 14
- Vendor-marker blockers: 2 (`vz_2024_q4`, `crm_2025_q4`)

## Required Output

Return candidate rows with `case_id`, `ticker`, `source_url`, `source_domain`, `source_type`, `expected_format`, `rights_notes`, and `blocked_reason` if any. Keep `commit_allowed=false`, `training_allowed=false`, and `raw_text_committed=false`.
