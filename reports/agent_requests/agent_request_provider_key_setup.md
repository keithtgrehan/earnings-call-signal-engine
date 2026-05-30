# Agent Request: Provider Key And License Setup

## Scope

Configure provider access only where Keith has keys and license terms that allow metadata or raw transcript/audio retrieval for the project assessment workflow.

## Current Provider Status

- `earningscall`: `EARNINGSCALL_API_KEY` missing; raw download disabled.
- `quartr`: `QUARTR_API_KEY` missing; raw download disabled.
- `aiera`: `AIERA_API_KEY` missing; raw download disabled.
- `fmp`: `FMP_API_KEY` missing; raw download disabled.
- `api_ninjas`: `API_NINJAS_API_KEY` missing; raw download disabled.
- `sec_edgar`: metadata-only, no transcript/audio raw pull configured.

## This Run

- Provider audit completed.
- EarningsCall first30 discovery checked 42 cases and emitted 84 provider asset status rows.
- Provider discovery emitted metadata/status candidates only.
- Raw provider pull attempted: false.
- Raw provider data committed: false.
- `data/acquisition/provider_first30_asset_candidates.csv` was refreshed from metadata-safe discovery output.

## Required Before Raw Provider Pull

- Add provider API key as an environment variable.
- Add a provider-specific license config under `data/provider_license_configs/`.
- Set `license_config_ref` in `data/provider_registry.yaml`.
- Set `raw_download_allowed=true` only if the license permits raw project-assessment downloads.
- Keep provider raw files Desktop-only under `/Users/keith/Desktop/earnings calls 100 samples`.
- Keep `training_allowed=false` unless explicit training rights are documented in `explicit_training_rights_ref`.
