from __future__ import annotations

from tools.providers.base import ProviderConfig
from tools.providers.earningscall_adapter import EarningsCallAdapter


def test_earningscall_provider_reports_not_configured_without_key(monkeypatch) -> None:
    monkeypatch.delenv("EARNINGSCALL_API_KEY", raising=False)
    adapter = EarningsCallAdapter(
        ProviderConfig(
            provider_id="earningscall",
            name="EarningsCall API",
            api_key_env="EARNINGSCALL_API_KEY",
            enabled=True,
        )
    )

    status = adapter.provider_status()
    metadata = adapter.get_transcript_metadata(case_id="jpm_2025_q4", ticker="JPM", fiscal_year="2025", fiscal_quarter="Q4")

    assert status["status"] == "NOT_CONFIGURED"
    assert metadata["metadata_status"] == "NOT_CONFIGURED"
    assert metadata["raw_download_allowed"] is False
