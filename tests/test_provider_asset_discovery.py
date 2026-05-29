from __future__ import annotations

from signal_engine.providers.base import ProviderConfig, ProviderStatus
from signal_engine.providers.sec_edgar_provider import SecEdgarProvider
from tools.run_provider_asset_discovery import discover_provider_assets


def test_provider_discovery_includes_sec_edgar_and_missing_key_statuses() -> None:
    rows = [{"case_id": "jpm_2025_q4", "ticker": "JPM", "company_name": "JPMorgan Chase & Co.", "exchange": "NYSE"}]

    result = discover_provider_assets(rows=rows, config=ProviderConfig(env={}), providers=[SecEdgarProvider()])

    assert result["provider_status"]["sec_edgar"] == ProviderStatus.CONFIGURED.value
    assert result["candidates"]
    assert result["candidates"][0]["source_type"] == "sec_edgar"
    assert result["candidates"][0]["asset_type"] == "sec_exhibit"


def test_provider_discovery_writes_schema_compatible_rows() -> None:
    rows = [{"case_id": "jpm_2025_q4", "ticker": "JPM", "company_name": "JPMorgan Chase & Co.", "exchange": "NYSE"}]

    result = discover_provider_assets(rows=rows, config=ProviderConfig(env={}), providers=[SecEdgarProvider()])

    row = result["candidates"][0]
    for field in ("candidate_id", "case_id", "ticker", "asset_type", "source_type", "provenance_hash"):
        assert row[field]
