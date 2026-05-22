from __future__ import annotations

from .base import DataSourceAdapter


class ManualLocalAdapter(DataSourceAdapter):
    source_type = "manual_local"
    default_rights_tier = "manual_supplied"
    default_license_summary = "Manual local source; operator must provide source URL/path, terms notes, and permission scope."

    def validate_terms(self) -> dict[str, object]:
        payload = super().validate_terms()
        payload["operator_attestation_required"] = True
        return payload
