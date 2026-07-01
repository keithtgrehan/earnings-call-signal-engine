from __future__ import annotations

AUDIO_REGISTRY_FIELDS = [
    "audio_asset_id",
    "case_id",
    "ticker",
    "local_path",
    "sha256",
    "source_url",
    "rights_status",
    "eval_allowed",
    "commit_allowed",
    "training_allowed",
    "approval_ref",
    "raw_audio_committed",
    "ffprobe_status",
    "duration_sec",
    "sample_rate_hz",
    "channels",
    "asr_status",
    "asr_text_path",
    "raw_asr_committed",
    "notes",
]

ASR_MANIFEST_FIELDS = [
    "asr_record_id",
    "case_id",
    "audio_asset_id",
    "audio_sha256",
    "backend",
    "status",
    "dependency_status",
    "asr_text_path",
    "asr_text_sha256",
    "segments_path",
    "cloud_upload",
    "raw_asr_committed",
    "raw_asr_text_committed",
    "notes",
]

ASR_SEGMENT_FIELDS = [
    "segment_id",
    "case_id",
    "audio_asset_id",
    "start_time_sec",
    "end_time_sec",
    "speaker",
    "text_sha256",
    "raw_text_committed",
]

AUDIO_ALIGNMENT_FIELDS = [
    "alignment_id",
    "case_id",
    "audio_asset_id",
    "transcript_asset_id",
    "audio_sha256",
    "transcript_sha256",
    "alignment_status",
    "alignment_method",
    "alignment_score",
    "matched_span_count",
    "matched_transcript_start_char",
    "matched_transcript_end_char",
    "partial_alignment",
    "review_required",
    "source_relation",
    "raw_text_committed",
    "notes",
]

AUDIO_RAG_OBJECT_FIELDS = [
    "audio_object_id",
    "case_id",
    "audio_asset_id",
    "transcript_chunk_id",
    "alignment_id",
    "source_sha256",
    "rights_status",
    "retrieval_ready",
    "raw_audio_committed",
    "raw_asr_committed",
]

FORBIDDEN_AUDIO_LABEL_FIELDS = {"emotion", "deception", "stress", "mental_state", "health", "biometric", "speaker_identity"}


def validate_no_forbidden_audio_labels(row: dict[str, str]) -> list[str]:
    present = sorted(field for field in FORBIDDEN_AUDIO_LABEL_FIELDS if field in row)
    return [f"forbidden audio label field {field}" for field in present]
