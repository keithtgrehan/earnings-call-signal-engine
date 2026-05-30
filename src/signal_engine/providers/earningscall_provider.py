from __future__ import annotations

from .base import BaseProvider


class EarningsCallProvider(BaseProvider):
    name = "earningscall"
    env_key = "EARNINGSCALL_API_KEY"
    requires_license_for_raw = True
