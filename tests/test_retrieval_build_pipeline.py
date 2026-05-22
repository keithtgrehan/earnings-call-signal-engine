from __future__ import annotations

import pytest

from signal_engine.retrieval import build_retrieval_objects_from_manifest


def _row(object_type: str) -> dict[str, object]:
    return {
        "object_id": f"case-1:{object_type}",
        "object_type": object_type,
        "case_id": "case-1",
        "ticker": "MNL",
        "company": "Manual Local Example",
        "fiscal_period": "FY2024_Q2",
        "source_type": "manual_local",
        "source_ref": "/tmp/manual.txt",
        "rights_tier": "manual_supplied",
        "raw_text_commit_allowed": False,
        "section": "qa",
        "provenance": {
            "source_path": "/tmp/manual.txt",
            "span_ids": ["case-1:turn:1"],
            "provenance_hash": "sha256:test",
        },
    }


def test_retrieval_build_prioritizes_evidence_objects() -> None:
    objects = build_retrieval_objects_from_manifest([_row("semantic_chunk"), _row("evidence_object")])
    assert [row["object_type"] for row in objects] == ["evidence_object", "semantic_chunk"]
    assert objects[0]["retrieval_priority"] == 1


def test_retrieval_build_requires_provenance() -> None:
    row = _row("evidence_object")
    row.pop("provenance")
    with pytest.raises(KeyError):
        build_retrieval_objects_from_manifest([row])
