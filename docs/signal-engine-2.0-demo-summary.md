# Signal Engine 2.0 Demo Summary

## Files Added

- `demo/signal_engine_2_0/support_demo_output.json`
- `demo/signal_engine_2_0/sales_demo_output.json`
- `demo/signal_engine_2_0/account_management_demo_output.json`
- `demo/signal_engine_2_0/demo_report.md`
- `demo/signal_engine_2_0/buyer_one_pager.md`

Updated for demo quality:

- `data/signal_engine_2_0/sample_support.json`
- `data/signal_engine_2_0/sample_sales.json`
- `data/signal_engine_2_0/sample_account_management.json`
- `src/signal_engine/text_features.py`

## How To Run Demo

```bash
python scripts/signal_engine_analyze.py --domain support data/signal_engine_2_0/sample_support.json
python scripts/signal_engine_analyze.py --domain sales data/signal_engine_2_0/sample_sales.json
python scripts/signal_engine_analyze.py --domain account_management data/signal_engine_2_0/sample_account_management.json
```

## Validation Status

- targeted Signal Engine 2.0 CLI commands run locally
- targeted Signal Engine 2.0 tests run locally
- legacy `tests/test_features.py` run locally to confirm the support-QA MVP still works

## Known Legacy Blocker

`make portfolio-ci` is still blocked by a missing legacy proof artifact at `outputs/LLY_2025_Q2_call08/metrics.json`.

This demo pack does not attempt to fix that legacy proof path because it is outside the Signal Engine 2.0 demo scope.

## Branch Readiness

This branch is demo-ready for the Signal Engine 2.0 scope.

It is not yet full legacy-CI clean because of the existing portfolio-proof blocker above.
