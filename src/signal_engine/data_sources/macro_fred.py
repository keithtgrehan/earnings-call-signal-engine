from __future__ import annotations

from .base import DataSourceAdapter


class MacroFredAdapter(DataSourceAdapter):
    source_type = "macro_fred"
    default_rights_tier = "official_public_terms_checked"
    default_license_summary = "FRED API source; series-level source-owner terms must be checked before storing or redistributing values."

    def fetch_metadata(self) -> dict[str, object]:
        payload = super().fetch_metadata()
        payload["series_level_terms_required"] = True
        payload["raw_series_values_default"] = "blocked_until_series_terms_checked"
        return payload
