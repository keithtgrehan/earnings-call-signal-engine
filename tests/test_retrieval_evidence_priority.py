from __future__ import annotations

import csv
from pathlib import Path

from tools.export_retrieval_objects import export_retrieval_objects


def test_export_retrieval_objects_includes_evidence_manifest_first(tmp_path: Path, monkeypatch) -> None:
    chunk_manifest = tmp_path / "chunks.csv"
    chunk_manifest.write_text(
        "chunk_id,case_id,ticker,asset_id,asset_type,chunk_type,section,speaker_role,source_sha256,text_sha256,local_chunk_path,start_char,end_char,start_time_sec,end_time_sec,rights_status,rag_eligible,raw_text_committed\n"
        f"chunk1,case1,JPM,asset1,transcript,semantic_fallback,unknown,unknown,sha256:{'a'*64},sha256:{'b'*64},/tmp/desktop/chunk.txt,1,10,,,safe_to_download,true,false\n",
        encoding="utf-8",
    )
    evidence_manifest = tmp_path / "evidence.csv"
    evidence_manifest.write_text(
        "evidence_id,chunk_id,case_id,ticker,object_type,chunk_type,source_sha256,text_sha256,local_chunk_path,start_char,end_char,rights_status,raw_text_committed\n"
        f"evidence1,chunk1,case1,JPM,evidence_object,guidance_statement,sha256:{'a'*64},sha256:{'c'*64},/tmp/desktop/chunk.txt,1,10,safe_to_download,false\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("tools.export_retrieval_objects.REPORT_PATH", tmp_path / "retrieval.md")

    summary = export_retrieval_objects(chunk_manifest=chunk_manifest, out_path=tmp_path / "objects.csv", evidence_manifest=evidence_manifest)

    rows = list(csv.DictReader((tmp_path / "objects.csv").open(newline="", encoding="utf-8")))
    assert summary["evidence_objects"] == 1
    assert rows[0]["object_type"] == "evidence_object"
    assert rows[0]["retrieval_priority"] == "1"
    assert rows[0]["raw_text_committed"] == "false"
