"""Canonical data contracts and ingestion for the multimodal engine."""

from .ingestion import DATASET_CONNECTORS, ingest_datasets
from .schemas import (
    DOMAIN_ALIASES,
    NORMALIZED_SCHEMA_VERSION,
    DatasetIngestionStatus,
    NormalizedRecord,
    Provenance,
    SegmentRecord,
    normalize_domain,
)

__all__ = [
    "DATASET_CONNECTORS",
    "DOMAIN_ALIASES",
    "NORMALIZED_SCHEMA_VERSION",
    "DatasetIngestionStatus",
    "NormalizedRecord",
    "Provenance",
    "SegmentRecord",
    "ingest_datasets",
    "normalize_domain",
]
