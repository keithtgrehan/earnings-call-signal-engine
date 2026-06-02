from __future__ import annotations

import json
from pathlib import Path

import pytest

from signal_engine.retrieval.object_metadata import (
    REQUIRED_METADATA_FIELDS,
    build_retrieval_object_metadata,
    stable_metadata_object_id,
    validate_retrieval_object_metadata_record,
    validate_retrieval_object_metadata_rows,
)
from tools.export_retrieval_object_metadata import export_retrieval_object_metadata


def _metadata_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "case_id": "hd_2025_q4",
        "object_id": "",
        "object_type": "event_aligned_chunk_metadata",
        "company": "The Home Depot, Inc.",
        "ticker": "HD",
        "fiscal_period": "2025 Q4",
        "source_type": "manual_local_transcript_chunk",
        "provenance_ref": "/safe/provenance/normalized_transcript.json",
        "source_hash": "sha256:" + "a" * 64,
        "text_hash": "sha256:" + "b" * 64,
        "normalized_transcript_hash": "sha256:" + "c" * 64,
        "provenance_hash": "sha256:" + "d" * 64,
        "section_label": "prepared_remarks",
        "speaker_role": "management",
        "topic": "guidance",
        "span_start_char": 10,
        "span_end_char": 20,
        "rights_tier": "safe_to_download",
        "retrieval_priority": 2,
        "content_included": False,
        "embeddings_included": False,
        "vector_db_included": False,
    }
    row.update(overrides)
    row["object_id"] = stable_metadata_object_id(row)
    return row


def test_retrieval_object_metadata_schema_is_metadata_only() -> None:
    schema = json.loads(Path("schemas/retrieval_object_metadata.schema.json").read_text(encoding="utf-8"))

    assert set(schema["required"]) == REQUIRED_METADATA_FIELDS
    assert schema["additionalProperties"] is False
    assert schema["properties"]["object_type"]["enum"] == [
        "semantic_chunk_metadata",
        "event_aligned_chunk_metadata",
        "evidence_object_metadata",
    ]
    assert "raw_text" not in schema["properties"]
    assert "chunk_text" not in schema["properties"]
    assert "embedding" not in schema["properties"]
    assert "vector" not in schema["properties"]


@pytest.mark.parametrize("forbidden_key", ["raw_text", "chunk_text", "transcriptText", "payload_text", "embedding", "vectors"])
def test_metadata_record_rejects_raw_or_vector_payload_keys(forbidden_key: str) -> None:
    row = _metadata_row()
    row[forbidden_key] = "blocked"

    errors = validate_retrieval_object_metadata_record(row)

    assert any(forbidden_key in error for error in errors)


def test_metadata_record_rejects_missing_provenance() -> None:
    row = _metadata_row(provenance_ref="")

    errors = validate_retrieval_object_metadata_record(row)

    assert any("provenance_ref" in error for error in errors)


def test_metadata_record_rejects_unstable_object_id() -> None:
    row = _metadata_row()
    row["object_id"] = "manual_object_id"

    errors = validate_retrieval_object_metadata_record(row)

    assert any("stable object_id" in error for error in errors)


def test_metadata_rows_reject_duplicate_object_ids() -> None:
    row = _metadata_row()

    errors = validate_retrieval_object_metadata_rows([row, dict(row)])

    assert any("duplicate object_id" in error for error in errors)


def test_metadata_builder_outputs_deterministic_metadata_only_record() -> None:
    first = build_retrieval_object_metadata(
        object_type="evidence_object_metadata",
        case_id="hd_2025_q4",
        company="The Home Depot, Inc.",
        ticker="HD",
        fiscal_period="2025 Q4",
        source_type="manual_local_transcript_evidence",
        provenance_ref="/safe/provenance/normalized_transcript.json",
        source_hash="sha256:" + "a" * 64,
        text_hash="sha256:" + "b" * 64,
        normalized_transcript_hash="sha256:" + "c" * 64,
        provenance_hash="sha256:" + "d" * 64,
        section_label="prepared_remarks",
        speaker_role="management",
        topic="guidance",
        span_start_char=10,
        span_end_char=20,
        rights_tier="safe_to_download",
    )
    second = build_retrieval_object_metadata(
        object_type="evidence_object_metadata",
        case_id="hd_2025_q4",
        company="The Home Depot, Inc.",
        ticker="HD",
        fiscal_period="2025 Q4",
        source_type="manual_local_transcript_evidence",
        provenance_ref="/safe/provenance/normalized_transcript.json",
        source_hash="sha256:" + "a" * 64,
        text_hash="sha256:" + "b" * 64,
        normalized_transcript_hash="sha256:" + "c" * 64,
        provenance_hash="sha256:" + "d" * 64,
        section_label="prepared_remarks",
        speaker_role="management",
        topic="guidance",
        span_start_char=10,
        span_end_char=20,
        rights_tier="safe_to_download",
    )

    assert first == second
    assert first["object_id"].startswith("rom_evidence_")
    assert set(first) == REQUIRED_METADATA_FIELDS
    assert first["content_included"] is False
    assert first["embeddings_included"] is False
    assert first["vector_db_included"] is False


def test_exporter_is_deterministic_and_reports_counts(tmp_path: Path) -> None:
    manifest = tmp_path / "retrieval_objects_manifest.csv"
    manifest.write_text(
        "object_id,object_type,case_id,ticker,company,fiscal_period,source_type,source_ref,section,speaker,topic,span_start_char,span_end_char,source_sha256,text_sha256,normalized_transcript_sha256,provenance_ref,provenance_hash,rights_tier,retrieval_priority,commit_allowed,raw_text_commit_allowed,raw_text_committed\n"
        f"old_event,event_aligned_chunk,hd_2025_q4,HD,The Home Depot Inc.,2025 Q4,manual_local_transcript_chunk,/not/exported/chunk.txt,prepared_remarks,management,guidance,10,20,sha256:{'a'*64},sha256:{'b'*64},sha256:{'c'*64},/safe/provenance/hd.json,sha256:{'d'*64},safe_to_download,2,false,false,false\n"
        f"old_evidence,evidence_object,hd_2025_q4,HD,The Home Depot Inc.,2025 Q4,manual_local_transcript_evidence,/not/exported/evidence.txt,prepared_remarks,management,guidance,10,20,sha256:{'a'*64},sha256:{'e'*64},sha256:{'c'*64},/safe/provenance/hd.json,sha256:{'f'*64},safe_to_download,1,false,false,false\n",
        encoding="utf-8",
    )
    out_path = tmp_path / "metadata.jsonl"
    report_path = tmp_path / "report.md"

    first = export_retrieval_object_metadata(source_manifest=manifest, out_path=out_path, report_path=report_path)
    first_payload = out_path.read_text(encoding="utf-8")
    second = export_retrieval_object_metadata(source_manifest=manifest, out_path=out_path, report_path=report_path)
    second_payload = out_path.read_text(encoding="utf-8")

    assert first == second
    assert first_payload == second_payload
    rows = [json.loads(line) for line in first_payload.splitlines()]
    assert [row["object_type"] for row in rows] == ["evidence_object_metadata", "event_aligned_chunk_metadata"]
    assert all("source_ref" not in row for row in rows)
    assert all("chunk.txt" not in line for line in first_payload.splitlines())
    assert first["counts_by_object_type"] == {"event_aligned_chunk_metadata": 1, "evidence_object_metadata": 1}
    assert first["counts_by_case_id"] == {"hd_2025_q4": 2}
    report = report_path.read_text(encoding="utf-8")
    assert "retrieval_object_scaffold_only" in report
    assert "No embeddings" in report
    assert "No vector DB" in report
    assert "No evaluated retrieval quality" in report


def test_committed_retrieval_object_metadata_export_validates() -> None:
    path = Path("data/retrieval/retrieval_object_metadata.jsonl")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert rows
    assert validate_retrieval_object_metadata_rows(rows) == []
