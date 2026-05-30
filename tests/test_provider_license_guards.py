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
        "raw_download_allowed": False,
        "license_config_ref": "",
        "training_allowed": False,
        "explicit_training_rights_ref": "",
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
    target = desktop / "provider" / "raw.txt"
    errors = validate_raw_pull(
        _config(raw_download_allowed=True, license_config_ref="license_configs/example.yaml"),
        target,
        workspace=desktop,
    )
    assert errors == []


def test_training_requires_explicit_rights(tmp_path: Path) -> None:
    desktop = tmp_path / "desktop"
    errors = validate_raw_pull(
        _config(raw_download_allowed=True, license_config_ref="license_configs/example.yaml", training_allowed=True),
        desktop / "raw.txt",
        workspace=desktop,
    )
    assert "training_requires_explicit_training_rights_ref" in errors
