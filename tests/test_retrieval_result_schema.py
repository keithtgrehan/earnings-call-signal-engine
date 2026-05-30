from __future__ import annotations

import json
from pathlib import Path


def test_retrieval_result_schema_requires_no_raw_text() -> None:
    schema = json.loads(Path("schemas/retrieval_result.schema.json").read_text(encoding="utf-8"))
    payload = {
        "query_id": "q1",
        "object_id": "obj1",
        "rank": 1,
        "score": 1.0,
        "retrieval_method": "local_bm25_metadata",
        "raw_text_returned": False,
        "citation_valid": True,
        "abstained": False,
        "claim_safety_status": "retrieved_metadata_only",
    }
    assert payload["raw_text_returned"] == schema["properties"]["raw_text_returned"]["const"]
    assert payload["claim_safety_status"] in schema["properties"]["claim_safety_status"]["enum"]
    assert set(schema["required"]).issubset(payload)
