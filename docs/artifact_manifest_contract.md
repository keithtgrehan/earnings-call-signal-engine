# Artifact Manifest Contract

Artifact manifests live beside generated reports when practical. The canonical schema is `schemas/artifact_manifest.schema.json`.

Required fields:

- `run_id`
- `git_sha`
- `command`
- `timestamp`
- `config_hash`
- `input_hashes`
- `output_hashes`
- `schema_versions`
- `environment_summary`
- `generated_by`
- `deterministic_core_version`

Use `python scripts/validate_artifact_manifest.py --path <manifest>` to validate a manifest. The default local check accepts a missing manifest as `NOT_READY` so fresh clones can run before reports are generated.
