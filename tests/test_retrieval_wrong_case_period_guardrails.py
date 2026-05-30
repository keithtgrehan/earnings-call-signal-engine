from __future__ import annotations

import csv
import json
from pathlib import Path

from signal_engine.retrieval.evaluate import evaluate_retrieval_objects


FIELDS = [
    "object_id",
    "object_type",
    "case_id",
    "ticker",
    "company",
    "fiscal_period",
    "source_type",
    "source_ref",
    "section",
    "speaker",
    "topic",
    "span_start_char",
    "span_end_char",
    "source_sha256",
    "text_sha256",
    "normalized_transcript_sha256",
    "provenance_ref",
    "provenance_hash",
    "rights_tier",
    "retrieval_priority",
    "commit_allowed",
    "raw_text_commit_allowed",
    "raw_text_committed",
]


def _row(object_id: str, case_id: str, ticker: str, period: str) -> dict[str, str]:
    return {
        "object_id": object_id,
        "object_type": "event_aligned_chunk",
        "case_id": case_id,
        "ticker": ticker,
        "company": "",
        "fiscal_period": period,
        "source_type": "chunk",
        "source_ref": f"/desktop/{object_id}.txt",
        "section": "prepared_remarks",
        "speaker": "management",
        "topic": "guidance",
        "span_start_char": "0",
        "span_end_char": "10",
        "source_sha256": "sha256:" + "a" * 64,
        "text_sha256": "sha256:" + "b" * 64,
        "normalized_transcript_sha256": "sha256:" + "c" * 64,
        "provenance_ref": "/desktop/normalized.json",
        "provenance_hash": "sha256:" + "d" * 64,
        "rights_tier": "safe_to_download",
        "retrieval_priority": "2",
        "commit_allowed": "false",
        "raw_text_commit_allowed": "false",
        "raw_text_committed": "false",
    }


def test_case_specific_queries_filter_wrong_case_before_ranking(tmp_path: Path) -> None:
    objects = tmp_path / "objects.csv"
    with objects.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerow(_row("right", "hd_2025_q4", "HD", "2025 Q4"))
        writer.writerow(_row("wrong", "cat_2025_q4", "CAT", "2025 Q4"))
    queries = tmp_path / "queries.jsonl"
    queries.write_text(
        json.dumps(
            {
                "query_id": "q",
                "query": "CAT guidance management",
                "case_id": "hd_2025_q4",
                "ticker": "HD",
                "fiscal_period": "2025 Q4",
                "expected_object_ids": ["right"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    summary = evaluate_retrieval_objects(objects, queries, limit=5)
    returned = [row["object_id"] for row in summary["results"] if not row["abstained"]]
    assert returned == ["right"]
    assert summary["wrong_case_ticker_period"] == 0
