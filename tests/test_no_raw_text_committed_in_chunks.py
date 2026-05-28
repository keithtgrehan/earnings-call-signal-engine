from __future__ import annotations

import csv
from pathlib import Path

from tools.build_event_chunks import build_event_chunks


def test_chunk_manifest_contains_hashes_paths_not_raw_phrase(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "desktop"
    phrase = "tiny synthetic raw chunk phrase"
    transcript = workspace / "case1" / "transcript" / "call.txt"
    transcript.parent.mkdir(parents=True)
    transcript.write_text(f"Prepared remarks\nCEO: {phrase}\nQuestion-and-Answer\nAnalyst: Question?\nCFO: Answer.", encoding="utf-8")
    registry = tmp_path / "registry.csv"
    registry.write_text(
        "case_id,ticker,company_name,asset_type,local_path,sha256,source_url,provenance_path,rights_status,eval_allowed,commit_allowed,training_allowed,approval_ref,registered_timestamp,notes\n"
        f"case1,JPM,Example,audio,{transcript},sha256:{'a'*64},https://ir.example.com,,safe_to_download,true,false,false,approval://test,2026-01-01T00:00:00+00:00,test\n".replace(",audio,", ",transcript,"),
        encoding="utf-8",
    )
    monkeypatch.setattr("tools.build_event_chunks.REPORT_PATH", tmp_path / "report.md")

    summary = build_event_chunks(registry_path=registry, workspace=workspace, out_path=tmp_path / "chunks.csv", evidence_out=tmp_path / "evidence.csv")

    assert summary["transcript_chunks"] > 0
    manifest = (tmp_path / "chunks.csv").read_text(encoding="utf-8")
    assert phrase not in manifest
    rows = list(csv.DictReader((tmp_path / "chunks.csv").open(newline="", encoding="utf-8")))
    assert all(Path(row["local_chunk_path"]).exists() for row in rows)
    assert all(row["raw_text_committed"] == "false" for row in rows)
