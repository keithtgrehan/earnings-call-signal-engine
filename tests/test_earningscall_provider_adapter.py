from __future__ import annotations

from tools.providers.base import ProviderConfig
from tools.providers.earningscall_adapter import EarningsCallAdapter


def test_earningscall_adapter_metadata_methods_are_fail_closed(monkeypatch) -> None:
    monkeypatch.setenv("EARNINGSCALL_API_KEY", "test-key")
    adapter = EarningsCallAdapter(
        ProviderConfig(
            provider_id="earningscall",
            name="EarningsCall API",
            api_key_env="EARNINGSCALL_API_KEY",
            raw_download_allowed=False,
            supports_audio=True,
        )
    )

    transcript = adapter.get_transcript_metadata(case_id="hd_2025_q4", ticker="HD", fiscal_year="2025", fiscal_quarter="Q4")
    audio = adapter.get_audio_metadata(case_id="hd_2025_q4", ticker="HD", fiscal_year="2025", fiscal_quarter="Q4")

    assert transcript["asset_type"] == "transcript"
    assert audio["asset_type"] == "audio"
    assert transcript["raw_download_allowed"] is False
    assert audio["raw_download_allowed"] is False
    assert transcript["metadata_status"] in {"SDK_MISSING", "METADATA_ONLY"}
