# NYSE 100 Media Corpus Status

- Total candidates found: 100
- Priority 1: 0
- Priority 2: 0
- Priority 3: 0
- Priority 4: 100
- Blocked/paywalled manifest cases: 0
- Blocked source-registry rows: 100
- Safe download candidates: 0
- Local output root: `/Users/keith/Desktop/earnings calls 100 samples`
- Validation status: passed

## Top Source Domains

| value | count |
|---|---|
| sec-edgar | 100 |
| youtube.com | 100 |
| licensed-vendor | 100 |
| jpmorganchase.com | 4 |
| stock.walmart.com | 4 |
| ir.homedepot.com | 4 |
| investor.jnj.com | 4 |
| corporate.exxonmobil.com | 4 |
| investor.bankofamerica.com | 4 |
| goldmansachs.com | 4 |
| morganstanley.com | 4 |
| ir.blackrock.com | 4 |
| ir.americanexpress.com | 4 |
| ibm.com | 4 |
| investor.lilly.com | 4 |

## Source Type Distribution

| value | count |
|---|---|
| company_ir | 100 |
| webcast_provider | 100 |
| sec_edgar | 100 |
| youtube_metadata_only | 100 |
| earnings_platform | 100 |

## Missing Media Distribution

| value | count |
|---|---|
| transcript_unknown | 100 |
| audio_unknown | 100 |
| video_unknown | 100 |

## Exchange Exclusions

| value | count |
|---|---|
| NASDAQ | 3 |

## Next 20 Manual Review Actions

- `abt_2025_q4` `company_ir`: Review official IR source terms and robots policy before any raw transcript use. (https://www.abbottinvestor.com/)
- `abt_2026_q1` `company_ir`: Review official IR source terms and robots policy before any raw transcript use. (https://www.abbottinvestor.com/)
- `aon_2025_q4` `company_ir`: Review official IR source terms and robots policy before any raw transcript use. (https://ir.aon.com/)
- `aon_2026_q1` `company_ir`: Review official IR source terms and robots policy before any raw transcript use. (https://ir.aon.com/)
- `axp_2025_q4` `company_ir`: Review official IR source terms and robots policy before any raw transcript use. (https://ir.americanexpress.com/)
- `axp_2026_q1` `company_ir`: Review official IR source terms and robots policy before any raw transcript use. (https://ir.americanexpress.com/)
- `ba_2025_q4` `company_ir`: Review official IR source terms and robots policy before any raw transcript use. (https://investors.boeing.com/)
- `ba_2026_q1` `company_ir`: Review official IR source terms and robots policy before any raw transcript use. (https://investors.boeing.com/)
- `bac_2025_q4` `company_ir`: Review official IR source terms and robots policy before any raw transcript use. (https://investor.bankofamerica.com/)
- `bac_2026_q1` `company_ir`: Review official IR source terms and robots policy before any raw transcript use. (https://investor.bankofamerica.com/)
- `blk_2025_q4` `company_ir`: Review official IR source terms and robots policy before any raw transcript use. (https://ir.blackrock.com/)
- `blk_2026_q1` `company_ir`: Review official IR source terms and robots policy before any raw transcript use. (https://ir.blackrock.com/)
- `bmy_2025_q4` `company_ir`: Review official IR source terms and robots policy before any raw transcript use. (https://investor.bms.com/)
- `bmy_2026_q1` `company_ir`: Review official IR source terms and robots policy before any raw transcript use. (https://investor.bms.com/)
- `cat_2025_q4` `company_ir`: Review official IR source terms and robots policy before any raw transcript use. (https://investors.caterpillar.com/)
- `cat_2026_q1` `company_ir`: Review official IR source terms and robots policy before any raw transcript use. (https://investors.caterpillar.com/)
- `cl_2025_q4` `company_ir`: Review official IR source terms and robots policy before any raw transcript use. (https://investor.colgatepalmolive.com/)
- `cl_2026_q1` `company_ir`: Review official IR source terms and robots policy before any raw transcript use. (https://investor.colgatepalmolive.com/)
- `cop_2025_q4` `company_ir`: Review official IR source terms and robots policy before any raw transcript use. (https://www.conocophillips.com/investor/)
- `cop_2026_q1` `company_ir`: Review official IR source terms and robots policy before any raw transcript use. (https://www.conocophillips.com/investor/)

## Legal And Technical Blockers

- Official IR source terms and robots policy are not reviewed in this metadata-only run.
- SEC rows are queued as metadata references only; no filing body download is enabled.
- Webcast provider replay access can be session-restricted or expire.
- YouTube media acquisition is blocked without explicit authorization.
- Licensed vendor content is blocked without a license config.

## Recommended Next Acquisition Targets

- Review official IR terms and robots policy for top-priority company IR domains.
- Enable SEC metadata fetch only with a descriptive User-Agent and <=10 requests/second rate limit.
- Manually register local transcript files by path and sha256 when source terms are unclear.
- Promote only rights-reviewed transcript bodies into local analysis workflows.

## Git Status Summary

```text
## codex/nyse-100-media-corpus-discovery...origin/main
AM data/acquisition/nyse_100_media_manifest.csv
AM data/acquisition/nyse_100_media_source_registry.csv
AM data/acquisition/nyse_100_media_targets.csv
A  docs/acquisition/nyse_100_media_corpus_plan.md
A  reports/nyse_100_media_corpus_status.json
A  reports/nyse_100_media_corpus_status.md
A  reports/nyse_100_media_progress_025.md
A  reports/nyse_100_media_progress_050.md
A  reports/nyse_100_media_progress_075.md
A  reports/nyse_100_media_validation_summary.json
A  reports/safe_download_candidates.md
A  scripts/validate_nyse_100_media_manifest.py
A  tests/test_discover_nyse_earnings_media.py
A  tests/test_validate_nyse_100_media_manifest.py
AM tools/discover_nyse_earnings_media.py
```
