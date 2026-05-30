# Agent Request: EarningsCall License Setup

## Scope

Enable EarningsCall provider access only after Keith confirms API access and raw transcript/audio download rights for this project assessment workflow.

## Current Status

- `EARNINGSCALL_API_KEY`: missing in this run.
- `license_config_ref`: missing in `data/provider_registry.yaml`.
- `raw_download_allowed`: false.
- `raw_transcript_download_allowed`: false.
- `raw_audio_download_allowed`: false.
- `training_allowed`: false.
- Raw storage root: `/Users/keith/Desktop/earnings calls 100 samples/provider_raw/earningscall`.
- Provider raw pull attempted: false.
- Provider raw committed: false.

## Required Setup Before Raw Pull

1. Set `EARNINGSCALL_API_KEY` in the local shell environment.
2. Copy `data/provider_license_configs/earningscall.example.yml` to a reviewed local config path under `data/provider_license_configs/`.
3. Update `data/provider_registry.yaml` with `license_config_ref`.
4. Set raw flags to true only if the reviewed license explicitly permits raw project-assessment downloads.
5. Keep `repo_commit_raw_files=false` and `raw_storage_root` under the Desktop workspace.
6. Keep `training_allowed=false` unless explicit training rights are documented in `explicit_training_rights_ref`.

## Blocked Until Complete

- Provider transcript raw downloads.
- Provider audio raw downloads.
- VZ/CRM vendor-marker raw source use through provider paths.
- Provider-derived training use.
