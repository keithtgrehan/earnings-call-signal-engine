from __future__ import annotations

import json
from pathlib import Path

from review.chunking import chunk_text, load_transcript_chunks, load_transcript_file


def test_chunk_ids_are_deterministic_and_parameter_sensitive(tmp_path: Path) -> None:
    text = "Management raised guidance. " * 80
    first = chunk_text(text, case_id="NVDA_2026_Q4", source_file="transcript.txt", chunk_size=220, overlap=20, min_chunk_length=50)
    second = chunk_text(text, case_id="NVDA_2026_Q4", source_file="transcript.txt", chunk_size=220, overlap=20, min_chunk_length=50)
    changed = chunk_text(text, case_id="NVDA_2026_Q4", source_file="transcript.txt", chunk_size=260, overlap=20, min_chunk_length=50)
    assert [row.chunk_id for row in first] == [row.chunk_id for row in second]
    assert [row.chunk_id for row in first] != [row.chunk_id for row in changed]


def test_overlap_behavior_preserves_overlapping_offsets() -> None:
    text = "One sentence. Two sentence. Three sentence. Four sentence. " * 20
    chunks = chunk_text(text, case_id="META_2025_Q4", source_file="transcript.txt", chunk_size=160, overlap=30, min_chunk_length=40)
    assert len(chunks) > 1
    assert chunks[1].start_offset is not None
    assert chunks[0].end_offset is not None
    assert chunks[1].start_offset < chunks[0].end_offset


def test_transcript_json_preserves_section_and_speaker(tmp_path: Path) -> None:
    path = tmp_path / "CASE_2025_Q1" / "processed" / "transcript_sectioned.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({"sections": [{"section": "qa", "speaker": "Analyst", "text": "Can you discuss demand uncertainty? " * 20}]}),
        encoding="utf-8",
    )
    chunks = load_transcript_file(path, chunk_size=300, overlap=0, min_chunk_length=20)
    assert chunks
    assert chunks[0].section == "qa"
    assert chunks[0].speaker == "Analyst"
    assert chunks[0].case_id == "CASE_2025_Q1"


def test_processed_event_chunks_are_preferred(tmp_path: Path) -> None:
    root = tmp_path / "data"
    event_path = root / "processed" / "chunks" / "ACME_2025_Q2.event_chunks.jsonl"
    event_path.parent.mkdir(parents=True)
    event_path.write_text(
        json.dumps(
            {
                "case_id": "ACME_2025_Q2",
                "object_id": "event_1",
                "text": "Analyst pressure around margin guidance.",
                "section": "qa",
                "speaker_role": "analyst",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    raw = root / "manual_cases" / "ACME_2025_Q2" / "raw" / "transcript.txt"
    raw.parent.mkdir(parents=True)
    raw.write_text("This fallback transcript should not be loaded when event chunks exist.", encoding="utf-8")
    chunks = load_transcript_chunks(root, min_chunk_length=1)
    assert len(chunks) == 1
    assert chunks[0].source_artifact == "ACME_2025_Q2.event_chunks.jsonl"
    assert chunks[0].section == "qa"
