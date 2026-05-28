from __future__ import annotations

from signal_engine.chunking.evidence_objects import build_evidence_objects


def test_evidence_objects_are_metadata_only() -> None:
    rows = build_evidence_objects(
        [
            {
                "chunk_id": "chunk1",
                "case_id": "case1",
                "ticker": "JPM",
                "chunk_type": "qa_pair",
                "source_sha256": "sha256:" + "a" * 64,
                "text_sha256": "sha256:" + "b" * 64,
                "local_chunk_path": "/tmp/desktop/chunk.txt",
                "start_char": "1",
                "end_char": "2",
                "rights_status": "safe_to_download",
            }
        ]
    )

    assert rows[0]["object_type"] == "evidence_object"
    assert rows[0]["raw_text_committed"] == "false"
    assert "text" not in rows[0]
