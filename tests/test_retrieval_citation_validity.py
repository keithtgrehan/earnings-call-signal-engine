from __future__ import annotations

import csv
import json
from pathlib import Path

from signal_engine.retrieval.evaluate import evaluate_retrieval_objects
from tests.test_retrieval_wrong_case_period_guardrails import FIELDS, _row


def test_citation_validity_requires_hashes_and_context(tmp_path: Path) -> None:
    objects = tmp_path / "objects.csv"
    with objects.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerow(_row("obj", "hd_2025_q4", "HD", "2025 Q4"))
    queries = tmp_path / "queries.jsonl"
    queries.write_text(
        json.dumps(
            {
                "query_id": "q",
                "query": "HD guidance management",
                "case_id": "hd_2025_q4",
                "ticker": "HD",
                "fiscal_period": "2025 Q4",
                "expected_object_ids": ["obj"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    summary = evaluate_retrieval_objects(objects, queries, limit=5)
    assert summary["citation_validity"] == 1.0
    assert summary["provenance_completeness"] == 1.0
    assert summary["results"][0]["provenance_hash"].startswith("sha256:")
