from __future__ import annotations

from pathlib import Path

from tools.providers.base import load_provider_registry


def test_provider_registry_priorities_and_defaults() -> None:
    providers = load_provider_registry(Path("data/provider_registry.yaml"))
    assert list(providers)[:3] == ["earningscall", "quartr", "aiera"]
    assert providers["earningscall"].raw_download_allowed is False
    assert providers["earningscall"].training_allowed is False
    assert providers["sec_edgar"].metadata_discovery_allowed is True


def test_provider_registry_has_no_raw_without_license() -> None:
    providers = load_provider_registry(Path("data/provider_registry.yaml"))
    for config in providers.values():
        if config.raw_download_allowed:
            assert config.license_config_ref
        if config.training_allowed:
            assert config.explicit_training_rights_ref
