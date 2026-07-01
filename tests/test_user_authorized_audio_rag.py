from __future__ import annotations

import csv
from pathlib import Path

from tools.build_user_authorized_audio_rag import build_user_authorized_audio_rag


def test_audio_rag_writes_zero_ready_report_when_no_audio(tmp_path: Path, monkeypatch) -> None:
    registry = tmp_path / "audio_registry.csv"
    registry.write_text(
        "case_id,ticker,company_name,asset_type,local_path,sha256,rights_status,eval_allowed,commit_allowed,training_allowed,approval_ref,registered_timestamp,notes\n",
        encoding="utf-8",
    )
    workspace = tmp_path / "desktop"
    workspace.mkdir()
    monkeypatch.setattr("tools.build_user_authorized_audio_rag.REPORT_DIR", tmp_path / "reports")

    summary = build_user_authorized_audio_rag(registry_path=registry, workspace=workspace, out_path=tmp_path / "audio_rag.csv")

    assert summary["audio_rag_records"] == 0
    assert summary["local_asr_used"] is False
    assert "0" in (tmp_path / "reports" / "user_authorized_audio_rag_readiness.md").read_text(encoding="utf-8")


def test_audio_rag_records_local_audio_without_cloud_asr(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "desktop"
    audio = workspace / "JPM_JPMorgan_Chase_Co" / "2025-12-31_FY2025_Q4" / "audio" / "call.mp3"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"ID3audio")
    registry = tmp_path / "audio_registry.csv"
    registry.write_text(
        "\n".join(
            [
                "case_id,ticker,company_name,asset_type,local_path,sha256,rights_status,eval_allowed,commit_allowed,training_allowed,approval_ref,registered_timestamp,notes",
                f"jpm_2025_q4,JPM,JPMorgan Chase & Co.,audio,{audio},sha256:{'a'*64},safe_to_download,true,false,false,approval://keith/test,2026-05-24T00:00:00+00:00,test",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("tools.build_user_authorized_audio_rag.REPORT_DIR", tmp_path / "reports")

    summary = build_user_authorized_audio_rag(registry_path=registry, workspace=workspace, out_path=tmp_path / "audio_rag.csv")

    assert summary["audio_rag_records"] == 1
    rows = list(csv.DictReader((tmp_path / "audio_rag.csv").open(newline="", encoding="utf-8")))
    assert rows[0]["asr_status"] == "todo_local_asr_not_available"
    assert rows[0]["raw_text_committed"] == "false"
