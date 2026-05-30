from __future__ import annotations

from pathlib import Path

from tools.providers.base import ProviderConfig, validate_raw_pull


def _config(**overrides) -> ProviderConfig:
    values = {
        "provider_id": "earningscall",
        "name": "EarningsCall API",
        "priority": 1,
        "api_key_env": "",
        "enabled": True,
        "metadata_discovery_allowed": True,
        "supports_transcripts": True,
        "supports_audio": True,
        "supports_slides": False,
        "supports_metadata_only": True,
        "raw_transcript_download_allowed": False,
        "raw_audio_download_allowed": False,
        "raw_download_allowed": False,
        "license_config_ref": "",
        "training_allowed": False,
        "explicit_training_rights_ref": "",
        "raw_storage_root": "",
        "rate_limit": "",
        "notes": "",
    }
    values.update(overrides)
    return ProviderConfig(**values)


def test_raw_pull_requires_license_raw_flag_and_desktop_target(tmp_path: Path) -> None:
    errors = validate_raw_pull(_config(), tmp_path / "raw.txt", workspace=tmp_path / "desktop")
    assert "license_config_ref_required" in errors
    assert "raw_download_allowed_false" in errors
    assert "raw_target_must_be_desktop_workspace" in errors


def test_raw_pull_accepts_guarded_desktop_output(tmp_path: Path) -> None:
    desktop = tmp_path / "desktop"
    desktop.mkdir()
    license_config = desktop / "license.yml"
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
    target = desktop / "provider" / "raw.txt"
    errors = validate_raw_pull(
        _config(raw_download_allowed=True, raw_transcript_download_allowed=True, license_config_ref=str(license_config)),
        target,
        workspace=desktop,
        asset_type="transcript",
    )
    assert errors == []


def test_training_requires_explicit_rights(tmp_path: Path) -> None:
    desktop = tmp_path / "desktop"
    errors = validate_raw_pull(
        _config(raw_download_allowed=True, license_config_ref="", training_allowed=True),
        desktop / "raw.txt",
        workspace=desktop,
    )
    assert "training_requires_explicit_training_rights_ref" in errors
