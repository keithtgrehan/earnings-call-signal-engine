# First30 Transcript Ingestion Plan

- Scope: NYSE first-30 transcript candidates plus the registered HD control fixture.
- Storage: raw PDFs/HTML/TXT and parsed transcript text stay under the Desktop workspace only.
- Repo policy: metadata manifests only; `commit_allowed=false`, `training_allowed=false`, `raw_text_committed=false`.

## Counts

- Candidate rows: 31
- Download-allowed rows: 8
- Rights-review-required rows: 31
- Q4CDN/CloudFront rows: 3
- Control fixture rows: 1

## Download Order

- 1. `vz_2024_q4` `VZ` official_direct review_required
- 2. `hd_2024_q3` `HD` official_direct review_required
- 3. `hd_2024_q2` `HD` official_direct review_required
- 4. `hd_2024_q1` `HD` official_direct review_required
- 5. `hd_2024_q4` `HD` official_direct review_required
- 10. `cat_2025_q4` `CAT` official_ir_cdn_direct review_required
- 15. `bac_2025_q4` `BAC` official_ir_cdn_direct review_required
- 16. `crm_2025_q4` `CRM` official_ir_cdn_direct review_required

## Blockers

- `control_fixture_already_registered`: 1
- `direct_transcript_url_required`: 22
- `download_allowed`: 8
