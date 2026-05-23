from __future__ import annotations


def estimation_window_readiness(*, prior_trading_days: int | None, market_data_available: bool) -> dict[str, object]:
    if not market_data_available:
        return {"status": "NOT_ENOUGH_DATA", "reason": "price/market/sector data unavailable", "calculation_run": False}
    if prior_trading_days is None or prior_trading_days < 120:
        return {"status": "NOT_ENOUGH_DATA", "reason": "requires at least 120 prior trading days", "calculation_run": False}
    return {"status": "READY", "required_prior_trading_days": 120, "calculation_run": False}
