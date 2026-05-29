from __future__ import annotations

from .base import BaseProvider, ProviderConfig, ProviderDiscoveryResult, ProviderStatus
from signal_engine.acquisition.asset_resolver import make_candidate


class SecEdgarProvider(BaseProvider):
    name = "sec_edgar"
    env_key = ""
    requires_license_for_raw = False

    def discover_assets(self, config: ProviderConfig, rows: list[dict[str, str]]) -> ProviderDiscoveryResult:
        candidates: list[dict[str, str]] = []
        for row in rows:
            if str(row.get("exchange", "NYSE")).upper() != "NYSE":
                continue
            source_url = row.get("filing_url") or f"https://data.sec.gov/submissions/CIK{row.get('cik', '0000000000')}.json"
            candidates.append(
                make_candidate(
                    row,
                    asset_type="sec_exhibit",
                    source_type="sec_edgar",
                    source_url=source_url,
                    resolved_asset_url=source_url,
                    confidence=0.5,
                    confidence_reason="SEC EDGAR metadata provider always available",
                    rights_status="metadata_only",
                    download_allowed=False,
                    next_action="resolve_sec_exhibits",
                )
            )
        return ProviderDiscoveryResult(self.name, ProviderStatus.CONFIGURED, candidates, "SEC EDGAR metadata available")
