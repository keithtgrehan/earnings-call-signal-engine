# Training Readiness

No model training was run. This report derives readiness from canonical readiness only.

## Canonical readiness authority

- Authoritative source: `reports/readiness_canonical.json`
- Status: `NOT_READY`
- Training: `BLOCKED`
- Training ready: `False`
- Strict-valid gold rows: `0` / `100`
- Training gate reason: `strict_valid_gold_count_below_100`
- Training attempted: `False`

## Training Blockers

- `strict_valid_gold_count_below_100`

## Repair Findings

- Legacy gold rows: `57`
- Blocked gold rows: `57`
- Repair candidates: `57`
- Repair required: `True`

## Training Plan Context

- Path: `configs/training_plan.example.yml`
- Status: `not_ready`
- Authority: `context_only`
