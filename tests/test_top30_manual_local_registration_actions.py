from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.build_top30_manual_local_registration_actions import build_top30, write_csv, write_report


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_top30_actions_stay_metadata_only_and_rights_closed(tmp_path: Path) -> None:
    transcript = tmp_path / "JPM_2026_Q1" / "raw" / "transcript.txt"
    transcript.parent.mkdir(parents=True)
    transcript.write_text("not read by this test\n", encoding="utf-8")
    discovery_path = tmp_path / "manual_local_discovery_candidates.jsonl"
    batch_path = tmp_path / "manual_local_batch_candidate.csv"
    nyse30_path = tmp_path / "nyse_30_pilot_targets.yml"
    csv_out = tmp_path / "top30.csv"
    report_out = tmp_path / "top30.md"
    _write_jsonl(
        discovery_path,
        [
            {
                "path_ref": str(transcript),
                "sha256": "sha256:abc",
                "size_bytes": 50_000,
                "body_parsed": False,
                "ocr_run": False,
            }
        ],
    )
    _write_csv(
        batch_path,
        [
            {
                "case_id": "jpm_2026_q1",
                "ticker": "JPM",
                "company_name": "",
                "fiscal_period": "2026_Q1",
                "local_path": str(transcript),
                "source_url": "",
                "source_type": "manual_local",
                "rights_tier": "unknown",
                "operator": "",
                "eval_allowed": "false",
                "training_allowed": "false",
                "commit_allowed": "false",
                "notes": "",
            }
        ],
    )
    nyse30_path.write_text(
        "targets:\n"
        "  - ticker: JPM\n"
        "    company_name: JPMorgan Chase & Co.\n",
        encoding="utf-8",
    )

    rows = build_top30(
        discovery_path=discovery_path,
        batch_path=batch_path,
        nyse30_path=nyse30_path,
        nyse100_path=tmp_path / "missing.csv",
        limit=30,
    )
    write_csv(csv_out, rows)
    write_report(report_out, rows, csv_out)

    assert len(rows) == 1
    row = rows[0]
    assert row["candidate_reason"].startswith("NYSE 30 target")
    assert row["source_sha256"] == "sha256:abc"
    assert row["rights_tier"] == "unknown"
    assert row["eval_allowed"] == "false"
    assert row["training_allowed"] == "false"
    assert row["commit_allowed"] == "false"
    assert row["registration_ready"] == "false"
    assert "not read by this test" not in csv_out.read_text(encoding="utf-8")
    report = report_out.read_text(encoding="utf-8")
    assert "Only run registration after removing any rows" in report
    assert "Do not copy raw transcript/audio/video files into the repository" in report
