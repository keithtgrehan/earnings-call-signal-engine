from __future__ import annotations

import csv
import json
from pathlib import Path

from tools.evaluate_retrieval import materialize_first30_queries
from tools.export_retrieval_objects import RETRIEVAL_MANIFEST_FIELDS


def test_materialize_first30_queries_prefers_evidence_objects(tmp_path: Path) -> None:
    objects = tmp_path / "objects.csv"
    with objects.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RETRIEVAL_MANIFEST_FIELDS, lineterminator="\n")
        writer.writeheader()
        base = {
            "case_id": "jpm_2025_q4",
            "ticker": "JPM",
            "company": "JPMorgan Chase",
            "fiscal_period": "2025 Q4",
            "source_type": "chunk",
            "source_ref": "/desktop/chunk.txt",
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
            "commit_allowed": "false",
            "raw_text_commit_allowed": "false",
            "raw_text_committed": "false",
        }
        writer.writerow({**base, "object_id": "fallback", "object_type": "semantic_chunk", "retrieval_priority": "3"})
        writer.writerow({**base, "object_id": "evidence", "object_type": "evidence_object", "retrieval_priority": "1"})
    out = tmp_path / "queries.jsonl"

    rows = materialize_first30_queries(objects, out)

    assert rows[0]["expected_object_ids"] == ["evidence"]
    assert rows[0]["expected_evidence_ids"] == ["evidence"]
    assert rows[0]["requires_evidence_object"] is True
    assert json.loads(out.read_text(encoding="utf-8").splitlines()[0])["query_id"] == "jpm_2025_q4_first30_metadata_smoke"
