from __future__ import annotations

from signal_engine.providers.base import ProviderConfig, ProviderStatus, StaticProvider


def test_missing_api_key_is_not_configured_not_failure() -> None:
    provider = StaticProvider(name="fmp", env_key="FMP_API_KEY", rows=[])

    result = provider.discover_assets(ProviderConfig(env={}), [])

    assert result.status == ProviderStatus.NOT_CONFIGURED
    assert result.candidates == []
    assert "FMP_API_KEY" in result.message


def test_vendor_raw_without_license_is_blocked() -> None:
    provider = StaticProvider(
        name="fmp",
        env_key="FMP_API_KEY",
        rows=[
            {
                "case_id": "jpm_2025_q4",
                "ticker": "JPM",
                "company_name": "JPMorgan Chase & Co.",
                "asset_type": "transcript_text",
                "source_url": "https://financialmodelingprep.com/api/v3/earning_call_transcript/JPM",
                "resolved_asset_url": "https://financialmodelingprep.com/api/v3/earning_call_transcript/JPM",
            }
        ],
    )

    result = provider.discover_assets(ProviderConfig(env={"FMP_API_KEY": "secret"}), [])

    assert result.status == ProviderStatus.BLOCKED
    assert result.candidates[0]["asset_type"] == "blocked"
    assert result.candidates[0]["blocked_reason"] == "vendor_raw_requires_license_config_ref"
    assert result.candidates[0]["download_allowed"] == "false"
