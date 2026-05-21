# Control Room 500-Call Rollout Review

Use this checklist before any corpus automation PR is merged.

## Safe Checks

```bash
make corpus-safe-check
python -m py_compile $(find src tools scripts -name "*.py")
pytest
ruff check . || true
git diff --check
```

## Stop Conditions

- Unknown or missing rights tier.
- Missing source terms, robots, paywall/login, or provenance fields.
- Raw transcript/audio/video staged without explicit rights.
- YouTube raw media download enabled by default.
- Licensed vendor raw ingest without explicit license config.
- External or weak-label rows written to gold.
- Alpha, trading, production ML, or statistical-significance claims.

## Rollout Status

This PR is a scaffold. It adds validators, metadata-only adapters, schema checks, and documentation. It does not acquire real data, train models, or call external APIs.
