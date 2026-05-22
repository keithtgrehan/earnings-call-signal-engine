from __future__ import annotations

from typing import Any

from .objects import build_retrieval_object


def build_retrieval_objects_from_manifest(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    for row in rows:
        raw_text_commit_allowed = row.get("raw_text_commit_allowed") is True
        object_type = str(row.get("object_type", "semantic_chunk"))
        evidence_text = str(row.get("evidence_text", "")) if raw_text_commit_allowed else ""
        redacted_preview = str(row.get("redacted_evidence_preview") or "[span reference only]")
        objects.append(
            build_retrieval_object(
                object_id=str(row["object_id"]),
                object_type=object_type,
                case_id=str(row["case_id"]),
                ticker=str(row.get("ticker", "")),
                company=str(row["company"]),
                fiscal_period=str(row["fiscal_period"]),
                source_type=str(row.get("source_type", "manual_local")),
                source_ref=str(row["source_ref"]),
                section=str(row.get("section", "unknown")),
                provenance=dict(row["provenance"]),
                rights_tier=str(row["rights_tier"]),
                commit_allowed=row.get("commit_allowed") is True,
                raw_text_commit_allowed=raw_text_commit_allowed,
                speaker=str(row.get("speaker", row.get("speaker_role", ""))),
                topic=str(row.get("topic", "")),
                span_hints=dict(row.get("span_hints") or {}),
                evidence_text=evidence_text,
                redacted_evidence_preview=redacted_preview,
                deterministic_signal_refs=list(row.get("deterministic_signal_refs") or []),
            )
        )
    return sorted(objects, key=lambda item: int(item["retrieval_priority"]))
