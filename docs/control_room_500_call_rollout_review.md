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
- Alpha, trading, causal, production ML, or statistical-significance claims.
- Event-study reports missing event date, estimation window, event window, expected return model, or controls.

## Agent Review Gates

Agent 5 acquisition gate:

- `500` calls are a target universe, not a forced ingest count.
- Every candidate has source type, media availability flags, terms/robots/paywall/login status, use permissions, provenance, and blocked reason.
- SEC/EDGAR settings remain fair-access compliant and conservatively rate limited.
- YouTube and vendor raw media/body ingest remains blocked by default.

Agent 2 evaluation gate:

- Event-study methodology records event date, estimation window, event window, expected return model, AR/CAR outputs, and controls.
- Reports include failure modes and coverage metrics.
- No causal, trading, alpha, or unsupported statistical-significance language is allowed.

## Rollout Status

This PR is a scaffold. It adds validators, metadata-only adapters, schema checks, and documentation. It does not acquire real data, train models, or call external APIs.
