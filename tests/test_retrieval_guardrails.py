from __future__ import annotations

import yaml


def test_retrieval_providers_disable_embeddings_and_vector_db_by_default() -> None:
    config = yaml.safe_load(open("configs/retrieval_providers.example.yml", encoding="utf-8"))

    assert config["defaults"]["provider_apis_enabled"] is False
    assert config["defaults"]["embeddings_enabled"] is False
    assert config["defaults"]["vector_db_commit_allowed"] is False
    assert config["local_bm25"]["commit_allowed"] is False
