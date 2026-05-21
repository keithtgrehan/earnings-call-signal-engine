from __future__ import annotations

from .base import DataSourceAdapter


class SecEdgarAdapter(DataSourceAdapter):
    source_type = "sec_edgar"
    default_rights_tier = "public_domain"
    default_license_summary = (
        "SEC EDGAR metadata/API source; follow SEC developer guidance, fair-access limits, and descriptive user-agent rules."
    )

    def fetch_metadata(self) -> dict[str, object]:
        payload = super().fetch_metadata()
        payload["fair_access_required"] = True
        payload["supported_default_scope"] = "companyfacts/submissions metadata only"
        return payload
