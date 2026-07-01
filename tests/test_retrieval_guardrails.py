from __future__ import annotations

import yaml

from signal_engine.retrieval.providers.config import REAL_PROVIDER_SLOTS


def test_retrieval_providers_disable_embeddings_and_vector_db_by_default() -> None:
    config = yaml.safe_load(open("configs/retrieval_providers.example.yml", encoding="utf-8"))

    assert config["status_label"] == "retrieval_provider_adapter_scaffold_only"
    assert config["default_provider"] == "local_stub"
    assert config["network_enabled"] is False
    assert config["providers"]["local_stub"]["enabled"] is True
    assert config["providers"]["local_stub"]["mode"] == "dry_run"
    assert config["providers"]["local_stub"]["network_enabled"] is False
    for slot in REAL_PROVIDER_SLOTS:
        assert config["providers"][slot]["enabled"] is False
        assert config["providers"][slot]["mode"] == "disabled"
        assert config["providers"][slot]["network_enabled"] is False
