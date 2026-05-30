# Agent Request: Replace Broken First30 Transcript URLs

## Scope

Find official/direct company-hosted transcript URLs for the unresolved NYSE first30 cases. Raw PDFs/text must remain Desktop-only. Do not use vendor transcript pages, paywalled/login sources, YouTube media, or signed/session URLs.

## Current Blockers

- `vz_2024_q4`: Verizon full-call PDF is company-hosted but contains Refinitiv StreetEvents vendor markers; blocked without `license_config_ref`.
- `crm_2025_q4`: Q4CDN PDF contains vendor copyright markers; blocked without `license_config_ref`.
- `jpm_2025_q4`, `jpm_2025_q3`, `jpm_2025_q2`: current rows are IR landing pages only; direct earnings-call transcript URL required. Automated same-domain probing found only mismatched `1q26` transcript URLs for these rows, so they were not applied.
- `cat_2025_q3`, `cat_2025_q2`, `cat_2025_q1`, `cat_2024_q4`: current rows are IR landing pages only; direct earnings-call transcript URL required.
- Remaining first30 Q4 rows for `DOW`, `EQT`, `F`, `HIG`, `LYB`, `OC`, `OMC`, `RDDT`, `RF`, `UBER`, and `VZ` 2025 quarters need direct official transcript URLs or safe replacements.

## Already Resolved

- `hd_2024_q1`, `hd_2024_q2`, `hd_2024_q3`, and `hd_2024_q4` were replaced with official Home Depot IR document URLs in the generated ingestion manifest.
- `bac_2025_q4` and `cat_2025_q4` parsed and registered from official IR CDN URLs.
- `jpm_2025_q1` was resolved to the direct official JPMC `1q25-earnings-transcript.pdf`, downloaded Desktop-only, parsed, and registered by path/hash only.

## Current Corpus Count

- Registered first30/control transcripts: 8
- Parsed first30 transcripts: 7 plus HD control fixture
- Download-allowed rows: 9
- Remaining direct-transcript URL blockers: 21

## Required Output

Return candidate rows with `case_id`, `ticker`, `source_url`, `source_domain`, `source_type`, `expected_format`, `rights_notes`, and `blocked_reason` if any. Keep `commit_allowed=false`, `training_allowed=false`, and `raw_text_committed=false`.
