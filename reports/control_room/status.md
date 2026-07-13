# Control Room Status

This status is generated from canonical readiness and existing validation reports. It does not execute training, retrieval, downloads, or provider calls.

- Status: `NOT_READY`
- Training: `BLOCKED`
- Training ready: `False`
- Strict-valid gold rows: `0` / `100`
- Strict-valid adjudicated labels (informational): `0`
- Legacy repair candidate rows: `57`
- Legacy repair manifest rows: `0`
- Promotion-eligible repair rows: `0`
- Training gate reason: `strict_valid_gold_count_below_100`

No provider APIs were called. No canonical gold rows were modified.

## Training Blockers

- `strict_valid_gold_count_below_100`

## Repair Findings

- Legacy gold rows: `57`
- Blocked gold rows: `57`
- Repair candidates: `57`
- Repair required: `True`
- Training gate impact: `none`

## Repair Manifest

- none

## Blocked Operations

- `canonical_gold_mutation`: `BLOCKED`
- `embeddings`: `BLOCKED`
- `model_training`: `BLOCKED`
- `provider_api_calls`: `BLOCKED`
- `raw_transcript_download`: `BLOCKED`

## Blocked Claims

- `alpha`: `BLOCKED`
- `causal_market_impact`: `BLOCKED`
- `production_ml`: `BLOCKED`
- `production_retrieval_quality`: `BLOCKED`
- `statistical_significance`: `BLOCKED`
- `trading_performance`: `BLOCKED`

## Reports

- `canonical_readiness`: `reports/readiness_canonical.json` exists=`True` status=`NOT_READY`
- `gold_label_audit`: `reports/gold_label_audit/gold_label_audit.json` exists=`True` status=`REFERENCE`
- `legacy_gold_repair_manifest`: `data/review/staging/legacy_gold_repair_manifest.jsonl` exists=`False` status=`MISSING`
- `training_readiness`: `reports/training_readiness.json` exists=`True` status=`REFERENCE`

## Next Actions

- Repair legacy gold provenance through human-reviewed staging, not direct canonical edits.
- Adjudicate enough strict-valid labels to reach the 100-label training gate.
- Keep source rights, artifact policy, and claims validators in the Control Room status loop.
