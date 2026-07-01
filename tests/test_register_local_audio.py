from __future__ import annotations

import csv
from pathlib import Path

from tools.register_local_audio import register_local_audio


def test_register_local_audio_hashes_desktop_audio_only(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "desktop"
    audio = workspace / "case1" / "audio" / "call.mp3"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"ID3tiny")
    input_csv = tmp_path / "input.csv"
    input_csv.write_text(
        "case_id,ticker,company_name,local_path,source_url,approval_ref,eval_allowed\n"
        f"case1,JPM,Example,{audio},https://ir.example.com,approval://test,true\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("tools.register_local_audio.REPORT_PATH", tmp_path / "report.md")

    summary = register_local_audio(input_csv=input_csv, workspace=workspace, out_path=tmp_path / "audio_registry.csv")

    assert summary["registered_audio"] == 1
    rows = list(csv.DictReader((tmp_path / "audio_registry.csv").open(newline="", encoding="utf-8")))
    assert rows[0]["commit_allowed"] == "false"
    assert rows[0]["training_allowed"] == "false"
    assert rows[0]["sha256"].startswith("sha256:")
