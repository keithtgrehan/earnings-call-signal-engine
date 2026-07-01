from __future__ import annotations


def control_readiness(*, has_market_data: bool = False, has_sector_data: bool = False, has_price_data: bool = False) -> dict[str, object]:
    ready = has_market_data and has_sector_data and has_price_data
    return {
        "status": "READY" if ready else "NOT_ENOUGH_DATA",
        "has_market_data": has_market_data,
        "has_sector_data": has_sector_data,
        "has_price_data": has_price_data,
        "no_market_data_fetch": True,
    }
