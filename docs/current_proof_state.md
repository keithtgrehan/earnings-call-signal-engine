# Current Proof State

## Merged Baseline

- PR #36 merged: best-in-class corpus/resource readiness scaffold.
- PR #37 merged: Agent 5 acquisition, Agent 4 review, and Agent 1 extraction automation.
- PR #38 merged: research registry validation.

## Built Now

- Deterministic Agent 1 candidate generation remains canonical.
- Agent 5 metadata-only source discovery and manual-local registration gates are present.
- Agent 4 review queue, contamination flags, calibration, packets, and promotion checks are present.
- `signal-engine doctor --json` and artifact manifest validation are present.

## Blockers

- Manual-local transcript registry may be empty until operator-supplied paths are registered.
- Canonical legacy rows present: `57`.
- Strict provenance-complete valid count from `scripts/audit_gold_labels.py`: `0` because current canonical rows are blocked on sha256 provenance.
- First-100 ranked review queue rows: `48`.
- Agent 1 registered-source candidate count: `0` until transcript paths are registered.
- Training readiness remains `NOT_READY` until valid adjudicated gold count is at least 100.
- Retrieval/RAG benchmark readiness is gated by registered transcript sources and evidence objects.
- Event-study evaluation is exploratory only and blocked without approved market data.

## Next Manual Actions

1. Register rights-cleared manual-local transcript paths with sha256 hashes.
2. Review first-100 candidate packets and adjudicate calibration batch.
3. Repair provenance for legacy canonical rows only through human-reviewed staging.
4. Re-run `make real-pilot-readiness-check`.
