from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any, Protocol

from signal_engine.retrieval.providers.config import ProviderSlotConfig
from signal_engine.retrieval.providers.safety import RETRIEVAL_PROVIDER_STATUS_LABEL, validate_provider_report_payload


@dataclass(frozen=True)
class ProviderRunMetadata:
    status_label: str
    provider_slot: str
    provider_type: str
    provider_mode: str
    dry_run: bool
    object_count: int
    counts_by_object_type: dict[str, int]
    counts_by_case_id: dict[str, int]
    object_metadata_digest: str
    config_path: str
    objects_path: str
    evaluated_retrieval_quality: bool = False
    embeddings_generated: bool = False
    vector_db_generated: bool = False
    network_calls: bool = False
    provider_benchmark_complete: bool = False
    production_rag_claim: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        errors = validate_provider_report_payload(payload)
        if errors:
            raise ValueError("; ".join(errors))
        return payload


class EmbeddingProvider(Protocol):
    slot_config: ProviderSlotConfig

    def dry_run_metadata(self, objects: list[dict[str, Any]], *, config_path: str, objects_path: str) -> ProviderRunMetadata:
        ...


class RerankingProvider(Protocol):
    slot_config: ProviderSlotConfig

    def dry_run_metadata(self, objects: list[dict[str, Any]], *, config_path: str, objects_path: str) -> ProviderRunMetadata:
        ...


def object_metadata_digest(objects: list[dict[str, Any]]) -> str:
    digest_rows = [
        {
            "case_id": row.get("case_id", ""),
            "object_id": row.get("object_id", ""),
            "object_type": row.get("object_type", ""),
            "provenance_hash": row.get("provenance_hash", ""),
            "text_hash": row.get("text_hash", ""),
        }
        for row in objects
    ]
    encoded = json.dumps(digest_rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def build_provider_run_metadata(
    *,
    slot_config: ProviderSlotConfig,
    objects: list[dict[str, Any]],
    config_path: str,
    objects_path: str,
) -> ProviderRunMetadata:
    return ProviderRunMetadata(
        status_label=RETRIEVAL_PROVIDER_STATUS_LABEL,
        provider_slot=slot_config.slot,
        provider_type=slot_config.provider_type,
        provider_mode=slot_config.mode,
        dry_run=True,
        object_count=len(objects),
        counts_by_object_type=dict(sorted(Counter(str(row.get("object_type", "")) for row in objects).items())),
        counts_by_case_id=dict(sorted(Counter(str(row.get("case_id", "")) for row in objects).items())),
        object_metadata_digest=object_metadata_digest(objects),
        config_path=config_path,
        objects_path=objects_path,
    )
