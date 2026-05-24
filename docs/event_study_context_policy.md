# Event Study Context Policy

Supported exploratory event windows:

- `[-1,+1]`
- `[0,+1]`
- `[0,+2]`

No event-study calculation runs unless required price, market, and sector inputs are available and approved. Estimation readiness requires at least 120 prior trading days.

Reports must include `NOT_ENOUGH_DATA`, `EXPLORATORY_ONLY`, `NO_SIGNIFICANCE_CLAIM`, `NO_CAUSAL_CLAIM`, and `NO_TRADING_CLAIM`.
