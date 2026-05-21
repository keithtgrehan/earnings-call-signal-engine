from __future__ import annotations

from .base import DataSourceAdapter


class CompanyIRAdapter(DataSourceAdapter):
    source_type = "company_ir"
    default_rights_tier = "official_public_terms_checked"
    default_license_summary = "Official investor-relations source; company site terms and robots rules must be checked per source."

    def fetch_metadata(self) -> dict[str, object]:
        payload = super().fetch_metadata()
        payload["terms_check_required"] = True
        payload["raw_transcript_default"] = "blocked_until_terms_checked"
        return payload
