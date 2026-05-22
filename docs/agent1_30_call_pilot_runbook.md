# Agent 1 30-Call Pilot Runbook

Run order:

```bash
make validate-nyse-30-pilot
make register-manual-local-batch
make validate-manual-local-registry
make agent1-pilot
make first-100-review-queue
```

Expected first run:

- `register-manual-local-batch` may report `NOT_READY` until a local batch manifest exists.
- `agent1-pilot` may produce zero candidates until transcript paths are registered.
- no raw transcript bodies are committed
- no canonical gold labels are written
- all Agent 1 rows remain candidates for human review

Manual-local transcript registration should use path and sha256 hash only. The source file stays outside committed repo data unless a separate rights review explicitly permits storage.
