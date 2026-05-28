from __future__ import annotations

import json
from pathlib import Path


def test_chunk_schema_includes_event_types() -> None:
    schema = json.loads(Path("schemas/nyse_100_chunk_manifest.schema.json").read_text(encoding="utf-8"))
    values = set(schema["properties"]["chunk_type"]["enum"])

    assert {"prepared_remarks", "qa_question", "qa_answer", "qa_pair", "evidence_object", "semantic_fallback"}.issubset(values)


def test_evidence_schema_forbids_raw_text_commit() -> None:
    schema = json.loads(Path("schemas/evidence_object.schema.json").read_text(encoding="utf-8"))

    assert schema["properties"]["raw_text_committed"]["const"] is False
