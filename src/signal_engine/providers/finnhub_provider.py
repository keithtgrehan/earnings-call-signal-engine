from __future__ import annotations

from .base import BaseProvider


class FinnhubProvider(BaseProvider):
    name = "finnhub"
    env_key = "FINNHUB_API_KEY"
    requires_license_for_raw = True
