from __future__ import annotations

from pathlib import Path

from tools.providers.base import ProviderConfig, validate_raw_pull


def test_earningscall_raw_transcript_requires_asset_specific_flag(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("EARNINGSCALL_API_KEY", "test-key")
    desktop = tmp_path / "desktop"
    license_config = tmp_path / "license.yml"
    license_config.write_text(
        "provider: EarningsCall\n"
        "license_config_ref: license.yml\n"
        "metadata_discovery_allowed: true\n"
        "raw_download_allowed: false\n"
        "raw_transcript_download_allowed: false\n"
        "raw_audio_download_allowed: false\n"
        "training_allowed: false\n"
        "repo_commit_raw_files: false\n"
        "raw_storage_root: /tmp/desktop\n"
        "license_review_status: pending\n",
        encoding="utf-8",
    )
    config = ProviderConfig(
        provider_id="earningscall",
        name="EarningsCall API",
        api_key_env="EARNINGSCALL_API_KEY",
        raw_download_allowed=True,
        raw_transcript_download_allowed=False,
        license_config_ref=str(license_config),
    )

    errors = validate_raw_pull(config, desktop / "provider_raw" / "call.txt", workspace=desktop, asset_type="transcript")

    assert "raw_transcript_download_allowed_false" in errors


def test_earningscall_raw_target_inside_repo_is_blocked(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("EARNINGSCALL_API_KEY", "test-key")
    config = ProviderConfig(
        provider_id="earningscall",
        name="EarningsCall API",
        api_key_env="EARNINGSCALL_API_KEY",
        raw_download_allowed=True,
        raw_transcript_download_allowed=True,
        license_config_ref="data/provider_license_configs/earningscall.example.yml",
    )

    errors = validate_raw_pull(config, Path("provider_raw.txt"), workspace=Path.cwd(), asset_type="transcript")

    assert "raw_target_must_not_be_inside_repo" in errors
