from __future__ import annotations

import csv
from pathlib import Path

from tools.discover_desktop_transcript_audio_assets import discover_desktop_assets


def test_discover_desktop_assets_writes_download_log_compatible_rows(tmp_path: Path) -> None:
    workspace = tmp_path / "desktop"
    call_dir = workspace / "JPM_JPMorgan_Chase_Co" / "2025-10-14_FY2025_Q3"
    transcript = call_dir / "transcript" / "jpm_q3_2025_transcript.txt"
    audio = call_dir / "audio" / "jpm_q3_2025_call.mp3"
    transcript.parent.mkdir(parents=True)
    audio.parent.mkdir(parents=True)
    transcript.write_text(
        "Operator: welcome to the earnings call.\n"
        "Corporate Participants\nJane CEO\nPrepared Remarks\n"
        "Question-and-Answer\nAnalyst: question\n",
        encoding="utf-8",
    )
    audio.write_bytes(b"audio")
    chunk = call_dir / "chunks" / "transcript" / "chunk.txt"
    chunk.parent.mkdir(parents=True)
    chunk.write_text("This generated chunk must not be rediscovered as a transcript.", encoding="utf-8")
    audit = workspace / "_audit" / "nyse_earnings_call_audit.csv"
    audit.parent.mkdir(parents=True)
    with audit.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "case_id",
                "ticker_symbol",
                "company_name",
                "exchange",
                "fiscal_year",
                "fiscal_quarter",
                "earnings_call_date",
                "transcript_local_path",
                "audio_local_path",
                "transcript_source_url",
                "audio_source_url",
                "rights_status",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "case_id": "jpm_2025_q3",
                "ticker_symbol": "JPM",
                "company_name": "JPMorgan Chase & Co.",
                "exchange": "NYSE",
                "fiscal_year": "2025",
                "fiscal_quarter": "Q3",
                "earnings_call_date": "2025-10-14",
                "transcript_local_path": str(transcript.parent),
                "audio_local_path": str(audio.parent),
                "transcript_source_url": "https://www.jpmorganchase.com/ir",
                "audio_source_url": "https://www.jpmorganchase.com/ir",
                "rights_status": "user_authorized_manual_local",
            }
        )

    out = workspace / "_audit" / "manual_local_desktop_asset_discovery.csv"
    summary = discover_desktop_assets(workspace=workspace, out_path=out)

    rows = list(csv.DictReader(out.open(newline="", encoding="utf-8")))
    assert summary["transcript_files"] == 1
    assert summary["audio_files"] == 1
    assert {row["asset_type"] for row in rows} == {"transcript", "audio"}
    assert {row["case_id"] for row in rows} == {"jpm_2025_q3"}
    assert all(row["download_status"] == "downloaded" for row in rows)
    assert all(row["sha256"].startswith("sha256:") for row in rows)
    assert all(row["commit_allowed"] == "false" and row["training_allowed"] == "false" for row in rows)
    assert all(Path(row["local_path"]).is_relative_to(workspace) for row in rows)
