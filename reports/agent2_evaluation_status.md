# Agent 2 Evaluation Status

Agent 2 event-study and evaluation gates are represented in the merged scaffold.

Current linked artifacts:

- `configs/event_study_cases.example.yml`
- `configs/event_study_join_policy.example.yml`
- `scripts/validate_event_study_cases.py`
- `scripts/validate_event_study_join_policy.py`
- `docs/claims_matrix_500_call_rollout.md`
- `docs/experiment_design_ab_multivariate.md`

Status:

- event-study cases are metadata-only
- no market data fetch is enabled
- AR/CAR framing remains exploratory
- significance claims are gated off by default
- no trading, alpha, causal, or live-execution claims are enabled
