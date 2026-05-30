from __future__ import annotations

from .base import BaseProvider


class FmpProvider(BaseProvider):
    name = "fmp"
    env_key = "FMP_API_KEY"
    requires_license_for_raw = True
