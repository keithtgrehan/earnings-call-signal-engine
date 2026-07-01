# Agent Request: Replace Broken First30 Transcript URLs

## Scope

Find clean official/direct company-hosted transcript URLs for unresolved NYSE first30 cases. Raw PDFs/text must remain Desktop-only. Do not use vendor transcript pages, paywalled/login sources, YouTube media, signed/session URLs, or vendor raw without `license_config_ref`.

## Current Corpus Count

- Registered first30/control transcripts: 31
- Clean parsed transcripts: 30
- Download-allowed rows: 30
- Remaining blocked original first30 rows: 12
- Vendor-marker blockers: 2
- Direct/safe transcript URL blockers: 10

## Newly Resolved In This Run

- Clean official/Q4CDN rows applied: `f_2025_q4`, `lyb_2025_q4`, `rddt_2025_q4`, `uber_2025_q4`.
- Clean alternate NYSE replacement rows applied: `f_2025_q1`, `f_2025_q2`, `f_2025_q3`, `lyb_2025_q1`, `lyb_2025_q2`, `lyb_2025_q3`, `rddt_2025_q2`, `rddt_2025_q3`, `jpm_2024_q1`, `jpm_2024_q2`, `jpm_2024_q3`, `jpm_2024_q4`.
- All newly download-allowed rows parsed and registered by path/hash only.

## Remaining Original First30 Blockers

- `vz_2024_q4`: Verizon full-call PDF is company-hosted but contains Refinitiv/StreetEvents markers; blocked without `license_config_ref` or a clean source.
- `crm_2025_q4`: Q4CDN PDF contains vendor copyright markers; blocked without `license_config_ref` or a clean source.
- `dow_2025_q4`: official IR Q4CDN transcript candidate detected but vendor marker blocked.
- `eqt_2025_q4`: official IR Q4CDN transcript candidate detected but vendor marker blocked.
- `hig_2025_q4`: official IR Q4CDN transcript candidate detected but vendor marker blocked.
- `oc_2025_q4`: official IR Q4CDN transcript candidate detected but vendor marker blocked.
- `omc_2025_q4`: official IR Q4CDN transcript candidate detected but vendor marker blocked.
- `rf_2025_q4`: official IR Q4CDN transcript candidate detected but vendor marker blocked.
- `vz_2025_q1`: official Verizon feed exposed a tokenized download URL; signed/session-style URL blocked.
- `vz_2025_q2`: no clean direct transcript URL found.
- `vz_2025_q3`: no clean direct transcript URL found.
- `vz_2025_q4`: official Verizon feed exposed a tokenized download URL; signed/session-style URL blocked.

## Required Output

Return candidate rows with `case_id`, `ticker`, `source_url`, `source_domain`, `source_type`, `expected_format`, `rights_notes`, and `blocked_reason` if any. Keep `commit_allowed=false`, `training_allowed=false`, and `raw_text_committed=false`.
