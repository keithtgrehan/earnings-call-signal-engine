# Canonical Readiness

Operational truth is strict and fail-closed. Legacy gold rows are repair candidates, not training-ready labels.

- Status: `NOT_READY`
- Gold source: `data/gold/gold_labels.jsonl`
- Total canonical gold rows: `57`
- Strict-valid training gate: `0` / `100`
- Strict-valid adjudicated labels (informational): `0`
- Legacy repair candidate rows: `57`
- Blocked gold rows (repair finding): `57`
- Training: `BLOCKED`
- Training ready: `False`
- Training gate reason: `strict_valid_gold_count_below_100`
- Canonical gold modified: `False`

No canonical gold rows were modified.

## Status Counts

- `BLOCKED_NO_PROVENANCE`: `57`

## Policy Gates

- `source_rights`: `FAIL_CLOSED` - Unknown or unrepaired legacy provenance is tracked separately from the strict training gate.
- `provenance`: `FAIL_CLOSED` - Only sha256-backed strict-valid rows can contribute to readiness.
- `artifact_policy`: `PASS` - No model weights, embeddings, raw transcript bodies, or provider outputs are produced.
- `claim_safety`: `PASS` - Alpha, trading performance, causal market impact, statistical significance, production ML, and production retrieval claims remain blocked.

## Training Blockers

- `strict_valid_gold_count_below_100`

## Repair Findings

- Legacy gold rows: `57`
- Blocked gold rows: `57`
- Repair candidates: `57`
- Repair required: `True`
- Training gate impact: `none`

### Blocked Status Counts

- `BLOCKED_NO_PROVENANCE`: `57`

## Next Actions

- Repair legacy gold provenance through human-reviewed staging, not direct canonical edits.
- Adjudicate enough strict-valid labels to reach the 100-label training gate.
- Keep source rights, artifact policy, and claims validators in the Control Room status loop.
