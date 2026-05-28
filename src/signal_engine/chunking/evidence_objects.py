from __future__ import annotations

from typing import Any

from .ids import stable_object_id


def build_evidence_objects(chunks: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for chunk in chunks:
        if chunk.get("chunk_type") not in {"qa_pair", "prepared_remarks", "guidance_statement", "guidance_revision_candidate"}:
            continue
        rows.append(
            {
                "evidence_id": stable_object_id(chunk.get("chunk_id", ""), chunk.get("text_sha256", ""), prefix="evidence"),
                "chunk_id": str(chunk.get("chunk_id", "")),
                "case_id": str(chunk.get("case_id", "")),
                "ticker": str(chunk.get("ticker", "")),
                "object_type": "evidence_object",
                "chunk_type": str(chunk.get("chunk_type", "")),
                "source_sha256": str(chunk.get("source_sha256", "")),
                "text_sha256": str(chunk.get("text_sha256", "")),
                "local_chunk_path": str(chunk.get("local_chunk_path", "")),
                "start_char": str(chunk.get("start_char", "")),
                "end_char": str(chunk.get("end_char", "")),
                "rights_status": str(chunk.get("rights_status", "")),
                "raw_text_committed": "false",
            }
        )
    return rows
