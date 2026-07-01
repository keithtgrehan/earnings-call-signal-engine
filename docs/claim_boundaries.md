# Claim Boundaries

Signal Engine may claim local readiness, deterministic candidate generation, review workflow status, metadata coverage, and evidence/provenance checks when validation passes.

It must not claim:

- alpha
- buy/sell recommendations
- live trading readiness
- causal effects
- statistical significance
- production ML readiness
- training readiness before valid adjudicated gold count is at least 100

Every evaluation/event-study report must include:

- `NOT_ENOUGH_DATA`
- `EXPLORATORY_ONLY`
- `NO_SIGNIFICANCE_CLAIM`
- `NO_CAUSAL_CLAIM`
- `NO_TRADING_CLAIM`
