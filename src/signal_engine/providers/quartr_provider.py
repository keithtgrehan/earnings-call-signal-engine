from __future__ import annotations

from .base import BaseProvider


class QuartrProvider(BaseProvider):
    name = "quartr"
    env_key = "QUARTR_API_KEY"
    requires_license_for_raw = True
