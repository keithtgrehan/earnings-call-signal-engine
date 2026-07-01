from __future__ import annotations

import csv
from pathlib import Path

from signal_engine.acquisition.nyse100 import build_desktop_chunks, build_rag_index_manifest


def test_chunking_only_processes_eval_allowed_registered_transcripts(tmp_path: Path) -> None:
    allowed = tmp_path / "JPM_JPMorgan_Chase_Co" / "2025-12-31_FY2025_Q4"
    blocked = tmp_path / "BAC_Bank_of_America_Corp" / "2025-12-31_FY2025_Q4"
    (allowed / "transcript").mkdir(parents=True)
    (allowed / "chunks").mkdir()
    (blocked / "transcript").mkdir(parents=True)
    (blocked / "chunks").mkdir()
    allowed_text = allowed / "transcript" / "manual.txt"
    blocked_text = blocked / "transcript" / "blocked.txt"
    allowed_text.write_text("A" * 1200, encoding="utf-8")
    blocked_text.write_text("B" * 1200, encoding="utf-8")

    registry = tmp_path / "registry.csv"
    with registry.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "case_id",
            "ticker",
            "local_path",
            "sha256",
            "rights_status",
            "eval_allowed",
            "commit_allowed",
            "training_allowed",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerow(
            {
                "case_id": "jpm_2025_q4",
                "ticker": "JPM",
                "local_path": str(allowed_text),
                "sha256": "sha256:" + "a" * 64,
                "rights_status": "manual_local_review_only",
                "eval_allowed": "true",
                "commit_allowed": "false",
                "training_allowed": "false",
            }
        )
        writer.writerow(
            {
                "case_id": "bac_2025_q4",
                "ticker": "BAC",
                "local_path": str(blocked_text),
                "sha256": "sha256:" + "b" * 64,
                "rights_status": "unknown_fail_closed",
                "eval_allowed": "false",
                "commit_allowed": "false",
                "training_allowed": "false",
            }
        )

    chunks = build_desktop_chunks(tmp_path, registry_path=registry)
    manifest_rows = build_rag_index_manifest(tmp_path, out_path=tmp_path / "chunk_manifest.csv")

    assert len(chunks) == 2
    assert len(manifest_rows) == 2
    assert {row["ticker"] for row in manifest_rows} == {"JPM"}
    assert all(row["raw_text_committed"] == "false" for row in manifest_rows)
    assert all(row["text_sha256"].startswith("sha256:") for row in manifest_rows)
    assert all(row["asset_type"] == "transcript" for row in manifest_rows)
    assert all(row["chunk_type"] == "transcript_text" for row in manifest_rows)
    assert all(row["rag_eligible"] == "true" for row in manifest_rows)
    assert all(Path(row["local_chunk_path"]).exists() for row in manifest_rows)
