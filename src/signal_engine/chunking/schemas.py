from __future__ import annotations

CHUNK_TYPES = {
    "prepared_remarks",
    "guidance_statement",
    "guidance_revision_candidate",
    "qa_question",
    "qa_answer",
    "qa_pair",
    "analyst_pressure_exchange",
    "management_hedging_span",
    "uncertainty_span",
    "reassurance_span",
    "answer_shift_candidate",
    "evidence_object",
    "semantic_fallback",
}

EVENT_CHUNK_MANIFEST_FIELDS = [
    "chunk_id",
    "case_id",
    "ticker",
    "asset_id",
    "asset_type",
    "chunk_type",
    "section",
    "speaker_role",
    "source_sha256",
    "text_sha256",
    "local_chunk_path",
    "start_char",
    "end_char",
    "start_time_sec",
    "end_time_sec",
    "rights_status",
    "rag_eligible",
    "raw_text_committed",
]

EVIDENCE_OBJECT_FIELDS = [
    "evidence_id",
    "chunk_id",
    "case_id",
    "ticker",
    "object_type",
    "chunk_type",
    "source_sha256",
    "text_sha256",
    "local_chunk_path",
    "start_char",
    "end_char",
    "rights_status",
    "raw_text_committed",
]
