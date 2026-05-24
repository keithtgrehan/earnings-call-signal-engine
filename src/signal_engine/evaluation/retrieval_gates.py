from __future__ import annotations

RETRIEVAL_METRICS = [
    "recall@k",
    "mrr",
    "evidence_id_hit_rate",
    "citation_validity",
    "blocked_source_count",
    "latency",
    "reviewer_usefulness",
]


def retrieval_gate_report(*, evidence_objects: int, registered_sources: int) -> dict[str, object]:
    ready = evidence_objects > 0 and registered_sources > 0
    return {
        "status": "READY" if ready else "NOT_ENOUGH_DATA",
        "metrics": RETRIEVAL_METRICS,
        "evidence_objects": evidence_objects,
        "registered_sources": registered_sources,
        "embeddings_built": False,
        "vector_db_built": False,
    }
