from __future__ import annotations

import json
from pathlib import Path

from signal_engine.transcripts import normalize_transcript_text
from tools.normalize_registered_transcripts import normalize_registered_transcripts


def test_normalized_schema_requires_repo_safe_fields() -> None:
    schema = json.loads(Path("schemas/normalized_transcript.schema.json").read_text(encoding="utf-8"))
    required = set(schema["required"])
    assert {"sections", "speaker_turns", "qa_pairs", "raw_sha256", "raw_text_committed"}.issubset(required)
    assert schema["properties"]["raw_text_committed"]["const"] is False


def test_normalizer_serializes_spans_and_hashes_without_raw_phrase() -> None:
    phrase = "tiny synthetic no-leak phrase"
    text = f"Prepared remarks\nCEO: We discuss guidance.\nQuestion-and-Answer\nAnalyst: {phrase}?\nCFO: We will follow up."
    normalized = normalize_transcript_text(text, case_id="jpm_2025_q4", ticker="JPM", company_name="Example Co")
    serialized = json.dumps(normalized, sort_keys=True)

    assert normalized["raw_text_committed"] is False
    assert normalized["sections"]
    assert normalized["speaker_turns"]
    assert phrase not in serialized
    assert "sha256:" in normalized["raw_sha256"]


def test_normalize_registered_transcripts_writes_desktop_json_only(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "desktop"
    raw = workspace / "CASE1" / "transcript" / "call.txt"
    raw.parent.mkdir(parents=True)
    raw.write_text("Prepared remarks\nCEO: Safe text.\nQuestion-and-Answer\nAnalyst: Question?\nCFO: Answer.", encoding="utf-8")
    registry = tmp_path / "registry.csv"
    registry.write_text(
        "case_id,ticker,company_name,asset_type,local_path,sha256,source_url,provenance_path,rights_status,eval_allowed,commit_allowed,training_allowed,approval_ref,registered_timestamp,notes\n"
        f"case1_2025_q1,JPM,Example Co,transcript,{raw},sha256:{'a'*64},https://ir.example.com,,safe_to_download,true,false,false,approval://test,2026-01-01T00:00:00+00:00,test\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("tools.normalize_registered_transcripts.REPORT_PATH", tmp_path / "report.md")

    summary = normalize_registered_transcripts(registry_path=registry, workspace=workspace, out_path=tmp_path / "manifest.csv")

    assert summary["normalized_transcripts"] == 1
    manifest = (tmp_path / "manifest.csv").read_text(encoding="utf-8")
    assert "Safe text" not in manifest
    normalized_path = workspace / "CASE1" / "metadata" / "normalized_transcript.json"
    assert normalized_path.exists()
    assert "Safe text" not in normalized_path.read_text(encoding="utf-8")
