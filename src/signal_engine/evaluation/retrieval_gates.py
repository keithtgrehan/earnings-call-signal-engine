from __future__ import annotations

RETRIEVAL_METRICS = [
    "recall@k",
    "mrr",
    "evidence_id_hit_rate",
    "citation_validity",
    "invalid_citation_rate",
    "abstention_correctness",
    "fallback_overuse_rate",
    "provenance_completeness_rate",
    "blocked_source_count",
    "latency",
    "reviewer_usefulness",
]

FIRST30_PROMOTION_REQUIRED_GATES = [
    "metadata_completeness",
    "raw_text_leak_checks",
    "qna_state_recorded",
    "fallback_ratio",
    "suppression_counts",
    "bm25_smoke_readiness",
    "recall_at_5",
    "mrr",
    "invalid_citation_rate",
    "abstention_correctness",
    "provenance_completeness_rate",
]


def retrieval_gate_report(*, evidence_objects: int, registered_sources: int) -> dict[str, object]:
    ready = evidence_objects > 0 and registered_sources > 0
    return {
        "status": "READY" if ready else "NOT_ENOUGH_DATA",
        "metrics": RETRIEVAL_METRICS,
        "evidence_objects": evidence_objects,
        "registered_sources": registered_sources,
        "evaluated_rag": False,
        "evaluated_rag_gate": "requires completed retrieval eval manifest and passing RAG v0 gates",
        "first30_promotion_required_gates": FIRST30_PROMOTION_REQUIRED_GATES,
        "audio_only_transcript_aligned_evidence": False,
        "audio_only_exclusion_policy": "Audio-only objects are excluded from transcript-aligned retrieval until matched to transcript spans.",
        "embeddings_built": False,
        "vector_db_built": False,
    }
