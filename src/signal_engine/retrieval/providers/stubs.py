from __future__ import annotations

from typing import Any

from signal_engine.retrieval.providers.adapters import ProviderRunMetadata, build_provider_run_metadata
from signal_engine.retrieval.providers.config import ProviderSlotConfig


class DryRunEmbeddingProvider:
    def __init__(self, slot_config: ProviderSlotConfig) -> None:
        self.slot_config = slot_config

    def dry_run_metadata(self, objects: list[dict[str, Any]], *, config_path: str, objects_path: str) -> ProviderRunMetadata:
        return build_provider_run_metadata(
            slot_config=self.slot_config,
            objects=objects,
            config_path=config_path,
            objects_path=objects_path,
        )


class DryRunRerankingProvider:
    def __init__(self, slot_config: ProviderSlotConfig) -> None:
        self.slot_config = slot_config

    def dry_run_metadata(self, objects: list[dict[str, Any]], *, config_path: str, objects_path: str) -> ProviderRunMetadata:
        return build_provider_run_metadata(
            slot_config=self.slot_config,
            objects=objects,
            config_path=config_path,
            objects_path=objects_path,
        )
