"""Event-aligned transcript chunking primitives."""

from .event_chunker import build_event_chunks_for_text
from .evidence_objects import build_evidence_objects
from .ids import stable_chunk_id, stable_object_id
from .schemas import CHUNK_TYPES, EVENT_CHUNK_MANIFEST_FIELDS
from .validate_chunks import validate_chunk_manifest_rows

__all__ = [
    "CHUNK_TYPES",
    "EVENT_CHUNK_MANIFEST_FIELDS",
    "build_event_chunks_for_text",
    "build_evidence_objects",
    "stable_chunk_id",
    "stable_object_id",
    "validate_chunk_manifest_rows",
]
