from __future__ import annotations

from .base import BaseProvider


class ApiNinjasProvider(BaseProvider):
    name = "api_ninjas"
    env_key = "API_NINJAS_KEY"
    requires_license_for_raw = True
