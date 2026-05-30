from __future__ import annotations

import csv
from pathlib import Path

from tools.download_provider_assets import download_provider_assets


def test_download_provider_assets_blocks_without_key_and_license(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("EARNINGSCALL_API_KEY", raising=False)
    registry = tmp_path / "registry.yml"
    registry.write_text(
        "providers:\n"
        "  earningscall:\n"
        "    name: EarningsCall API\n"
        "    priority: 1\n"
        "    api_key_env: EARNINGSCALL_API_KEY\n"
        "    enabled: true\n"
        "    metadata_discovery_allowed: true\n"
        "    raw_download_allowed: false\n"
        "    raw_transcript_download_allowed: false\n"
        "    raw_audio_download_allowed: false\n"
        "    license_config_ref: ''\n"
        "    training_allowed: false\n",
        encoding="utf-8",
    )
    assets = tmp_path / "assets.csv"
    fields = ["provider", "case_id", "ticker", "fiscal_year", "fiscal_quarter", "asset_type", "metadata_status", "download_status", "raw_download_allowed", "license_config_ref", "training_allowed", "provider_url", "raw_storage_root", "notes"]
    with assets.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerow({"provider": "earningscall", "case_id": "jpm_2025_q4", "ticker": "JPM", "asset_type": "transcript"})

    summary = download_provider_assets(registry_path=registry, assets_in=assets, workspace=tmp_path / "desktop", audit_dir=tmp_path / "desktop" / "_audit")

    assert summary["download_attempts"] == 0
    assert summary["blocked_rows"] == 1
    assert (tmp_path / "desktop" / "_audit" / "provider_raw_download_log.csv").exists()
