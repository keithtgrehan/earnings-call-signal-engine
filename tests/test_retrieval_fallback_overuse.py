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


def _row(object_id: str, object_type: str, priority: str) -> dict[str, str]:
    return {
        "object_id": object_id,
        "object_type": object_type,
        "case_id": "hd_2025_q4",
        "ticker": "HD",
        "company": "Home Depot",
        "fiscal_period": "2025 Q4",
        "source_type": "chunk",
        "source_ref": f"/desktop/{object_id}.txt",
        "section": "prepared_remarks",
        "speaker": "management",
        "topic": "guidance",
        "span_start_char": "0",
        "span_end_char": "10",
        "source_sha256": "sha256:" + "a" * 64,
        "text_sha256": "sha256:" + object_id[0] * 64,
        "normalized_transcript_sha256": "sha256:" + "c" * 64,
        "provenance_ref": "/desktop/normalized.json",
        "provenance_hash": "sha256:" + priority * 64,
        "rights_tier": "safe_to_download",
        "retrieval_priority": priority,
        "commit_allowed": "false",
        "raw_text_commit_allowed": "false",
        "raw_text_committed": "false",
    }


def test_evidence_required_queries_do_not_return_semantic_fallback_padding(tmp_path: Path) -> None:
    objects = tmp_path / "objects.csv"
    with objects.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerow(_row("evidence", "evidence_object", "1"))
        writer.writerow(_row("fallback", "semantic_chunk", "3"))
    queries = tmp_path / "queries.jsonl"
    queries.write_text(
        json.dumps(
            {
                "query_id": "q",
                "query": "HD guidance prepared remarks",
                "case_id": "hd_2025_q4",
                "ticker": "HD",
                "fiscal_period": "2025 Q4",
                "expected_object_ids": ["evidence"],
                "expected_evidence_ids": ["evidence"],
                "requires_evidence_object": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    summary = evaluate_retrieval_objects(objects, queries, limit=10)

    assert [row["object_id"] for row in summary["results"] if not row["abstained"]] == ["evidence"]
    assert summary["fallback_overuse"] == 0.0
