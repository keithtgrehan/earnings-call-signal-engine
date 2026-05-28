from __future__ import annotations

import csv
from pathlib import Path

from tools.export_retrieval_objects import export_retrieval_objects


def test_export_retrieval_objects_uses_metadata_only(tmp_path: Path, monkeypatch) -> None:
    chunk_manifest = tmp_path / "chunks.csv"
    chunk_manifest.write_text(
        "chunk_id,case_id,ticker,asset_id,asset_type,chunk_type,section,speaker_role,source_sha256,text_sha256,local_chunk_path,start_char,end_char,start_time_sec,end_time_sec,rights_status,rag_eligible,raw_text_committed\n"
        f"chunk1,case1,JPM,asset1,transcript,qa_pair,qa,mixed,sha256:{'a'*64},sha256:{'b'*64},/tmp/desktop/chunk.txt,1,10,,,safe_to_download,true,false\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("tools.export_retrieval_objects.REPORT_PATH", tmp_path / "retrieval.md")

    summary = export_retrieval_objects(chunk_manifest=chunk_manifest, out_path=tmp_path / "objects.csv")

    assert summary["retrieval_objects"] == 1
    rows = list(csv.DictReader((tmp_path / "objects.csv").open(newline="", encoding="utf-8")))
    assert rows[0]["raw_text_commit_allowed"] == "false"
    assert rows[0]["raw_text_committed"] == "false"
    assert "phrase" not in (tmp_path / "objects.csv").read_text(encoding="utf-8")
