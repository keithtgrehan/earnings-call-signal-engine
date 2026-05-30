# Provider License Configs

Provider raw transcript or audio pulls are disabled until a provider-specific license config is added here and referenced from `data/provider_registry.yaml`.

Required config fields for raw provider pulls:

- `provider`
- `license_config_ref`
- `raw_download_allowed: true`
- `desktop_output_root`
- `training_allowed: false` unless `explicit_training_rights_ref` is populated

Raw provider data must be written only under `/Users/keith/Desktop/earnings calls 100 samples` and must never be committed to git.
