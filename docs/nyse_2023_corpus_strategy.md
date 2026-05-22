# NYSE 2023+ Corpus Strategy

Status: scaffold only. No real call acquisition, raw transcript download, audio/video download, scraping run, model training, provider API call, or market-data fetch has been performed.

## Target Universe

NYSE earnings calls from 2023 onward are a target universe, not a forced ingest list. A case can be registered only as metadata until source rights, source terms, robots/paywall/login status, provenance, and storage permissions are represented.

Each case must carry:

- `case_id`, `ticker`, `company_name`, `exchange`, `fiscal_period`, `call_date`, and `call_datetime`
- transcript, audio, and video availability flags
- source candidate metadata
- rights status and blocked reason
- raw transcript/audio/video allowed flags
- commit, training, and evaluation allowed flags
- robots and source-terms checks
- paywall/login status
- quality flags and provenance completeness

Unknown rights fail closed. Raw ingest cannot be requested when rights are unknown, restricted, paywalled, login-gated, or vendor-controlled. YouTube remains metadata-only unless explicit authorization is configured. Licensed vendor sources remain blocked unless license configuration explicitly permits raw ingest.

## Built Scaffold

- `configs/nyse_earnings_universe.example.yml` provides synthetic metadata-only rows.
- `schemas/nyse_earnings_universe.schema.json` records required fields.
- `scripts/validate_nyse_earnings_universe.py` fails closed on missing fields or unsafe raw-ingest flags.
- `scripts/build_nyse_earnings_universe.py` can build metadata rows from a user-supplied ticker CSV without network calls.

## Gated Future Work

Real acquisition requires reviewed source policy, rate limiting, blocked-case tracking, and no raw-body commit path. SEC/EDGAR access must stay fair-access compliant. Official IR pages require source-terms checks. Manual-local files may be registered by path and provenance hash, but raw files are not copied into the repo by default.
