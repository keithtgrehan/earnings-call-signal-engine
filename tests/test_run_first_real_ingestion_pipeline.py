from __future__ import annotations

import csv
from pathlib import Path

from tools.run_first_real_ingestion_pipeline import run_first_real_ingestion_pipeline


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_first_real_pipeline_processes_manual_local_pair_end_to_end(tmp_path: Path) -> None:
    workspace = tmp_path / "desktop"
    acquisition_dir = tmp_path / "repo" / "data" / "acquisition"
    corpus_dir = tmp_path / "repo" / "data" / "corpus"
    retrieval_dir = tmp_path / "repo" / "data" / "retrieval"
    local_dir = tmp_path / "repo" / ".local"
    call_dir = workspace / "JPM_JPMorgan_Chase_Co" / "2025-10-14_FY2025_Q3"
    transcript = call_dir / "transcript" / "jpm_q3_2025_transcript.txt"
    audio = call_dir / "audio" / "jpm_q3_2025_call.mp3"
    transcript.parent.mkdir(parents=True)
    audio.parent.mkdir(parents=True)
    transcript.write_text(
        "Operator: Good morning and welcome to the Q3 earnings call.\n"
        "Corporate Participants\nJane CEO\nJohn CFO\n"
        "Prepared Remarks\nWe are raising our full-year revenue guidance.\n"
        "Question-and-Answer\nAnalyst: What changed in demand?\n"
        "Jane CEO: Demand improved through the quarter.\n",
        encoding="utf-8",
    )
    audio.write_bytes(b"audio bytes")
    _write_csv(
        workspace / "_audit" / "nyse_earnings_call_audit.csv",
        [
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
        ],
    )
    _write_csv(
        acquisition_dir / "nyse_100_company_universe.csv",
        [{"ticker": "JPM", "company_name": "JPMorgan Chase & Co.", "exchange": "NYSE", "sector": "banking"}],
    )
    _write_csv(
        acquisition_dir / "nyse_100_5y_call_targets.csv",
        [{"case_id": "jpm_2025_q3", "ticker": "JPM", "company_name": "JPMorgan Chase & Co.", "exchange": "NYSE", "fiscal_year": "2025", "fiscal_quarter": "Q3", "event_date": "2025-10-14"}],
    )
    _write_csv(
        acquisition_dir / "nyse_100_source_rights_review_queue.csv",
        [{"case_id": "jpm_2025_q3", "ticker": "JPM", "company_name": "JPMorgan Chase & Co.", "fiscal_year": "2025", "fiscal_quarter": "Q3", "asset_type": "transcript", "source_url": "https://ir.example.com", "source_type": "official_ir"}],
    )

    summary = run_first_real_ingestion_pipeline(
        workspace=workspace,
        acquisition_dir=acquisition_dir,
        corpus_dir=corpus_dir,
        retrieval_dir=retrieval_dir,
        local_index_dir=local_dir / "bm25",
        target_pairs=1,
        official_resolver=lambda _rows: [],
        sec_resolver=lambda _rows: [],
        provider_resolver=lambda _rows: [],
        direct_detector=lambda row: row,
    )

    assert summary["manual_local_transcript_files"] == 1
    assert summary["manual_local_audio_files"] == 1
    assert summary["registered_transcripts"] == 1
    assert summary["registered_audio"] == 1
    assert summary["normalized_transcripts"] == 1
    assert summary["chunks"] > 0
    assert summary["evidence_objects"] > 0
    assert summary["retrieval_objects"] > 0
    assert summary["audio_rag_records"] == 1
    assert (workspace / "_audit" / "final_first_real_ingestion_status.json").exists()
