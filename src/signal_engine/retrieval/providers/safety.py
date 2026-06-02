from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from signal_engine.retrieval.object_metadata import validate_no_forbidden_metadata_payload_keys

RETRIEVAL_PROVIDER_STATUS_LABEL = "retrieval_provider_adapter_scaffold_only"

FORBIDDEN_PROVIDER_OUTPUT_KEYS = {
    "raw_text",
    "raw_transcript_text",
    "transcript_text",
    "asr_text",
    "audio_text",
    "chunk_text",
    "chunk_body_text",
    "payload_text",
    "retrieval_payload_text",
    "embedding",
    "embeddings",
    "embedding_values",
    "vector",
    "vectors",
    "vector_db",
    "index",
    "index_path",
    "faiss_index",
    "chroma_collection",
    "lancedb_table",
}

RESTRICTED_OUTPUT_COMPONENTS = {
    "raw",
    "asr",
    "audio",
    "transcripts",
    "provider_artifacts",
    "embeddings",
    "embedding",
    "vectors",
    "vector",
    "vector_db",
    "vectorstores",
    "faiss",
    "chroma",
    "lancedb",
    "indexes",
    "indices",
    "labels",
    "gold_labels",
    "adjudication",
    "training",
    "promotion",
}

FORBIDDEN_OUTPUT_NAME_RE = re.compile(r"(embedding|embeddings|vector|vectors|index|faiss|chroma|lancedb)", re.IGNORECASE)


def _compact_key(value: str) -> str:
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()
    return re.sub(r"[^a-z0-9]", "", snake)


def validate_provider_output_payload(payload: Any, *, context: str = "provider output") -> list[str]:
    errors = validate_no_forbidden_metadata_payload_keys(payload, context=context)
    forbidden = {_compact_key(key) for key in FORBIDDEN_PROVIDER_OUTPUT_KEYS}

    def visit(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                key_path = f"{path}.{key}" if path else str(key)
                if _compact_key(str(key)) in forbidden:
                    errors.append(f"{context}: forbidden provider output key {key_path}")
                visit(nested, key_path)
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                visit(nested, f"{path}[{index}]")

    visit(payload, "")
    return errors


def validate_provider_report_payload(payload: dict[str, Any]) -> list[str]:
    errors = validate_provider_output_payload(payload, context="provider run metadata")
    expected_false = (
        "evaluated_retrieval_quality",
        "embeddings_generated",
        "vector_db_generated",
        "network_calls",
        "provider_benchmark_complete",
        "production_rag_claim",
    )
    if payload.get("status_label") != RETRIEVAL_PROVIDER_STATUS_LABEL:
        errors.append(f"status_label must be {RETRIEVAL_PROVIDER_STATUS_LABEL!r}")
    for field in expected_false:
        if payload.get(field) is not False:
            errors.append(f"{field} must be false")
    if payload.get("dry_run") is not True:
        errors.append("dry_run must be true")
    return errors


def validate_safe_provider_output_path(path: Path) -> list[str]:
    errors: list[str] = []
    normalized_parts = {part.lower() for part in path.parts}
    blocked_components = sorted(normalized_parts & RESTRICTED_OUTPUT_COMPONENTS)
    if blocked_components:
        errors.append(f"output path uses restricted component(s): {', '.join(blocked_components)}")
    if FORBIDDEN_OUTPUT_NAME_RE.search(path.name):
        errors.append(f"output filename suggests generated embeddings/vectors/index artifacts: {path.name}")
    if path.suffix.lower() not in {".json", ".md"}:
        errors.append("provider dry-run output must use .json or .md")
    return errors
