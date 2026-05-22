from __future__ import annotations

from .base import DataSourceAdapter


class LicensedVendorAdapter(DataSourceAdapter):
    source_type = "licensed_vendor"
    default_rights_tier = "restricted"
    default_license_summary = (
        "Licensed/vendor transcript source; raw ingest is blocked until explicit license configuration permits every requested use."
    )

    def __init__(self, *args: object, license_config_permits_raw: bool = False, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.license_config_permits_raw = license_config_permits_raw

    def fetch_metadata(self) -> dict[str, object]:
        payload = super().fetch_metadata()
        payload["license_config_permits_raw"] = self.license_config_permits_raw
        payload["raw_vendor_body_default"] = "blocked"
        return payload

    def fetch_raw_if_allowed(self) -> dict[str, object]:
        if not self.license_config_permits_raw:
            return self.emit_blocked_case("Licensed vendor raw ingest blocked without explicit license config.")
        return super().fetch_raw_if_allowed()
