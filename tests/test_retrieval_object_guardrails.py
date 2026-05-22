from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from signal_engine.retrieval import build_retrieval_object, retrieval_priority_for_type, validate_retrieval_object

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_retrieval_objects.py"


def test_retrieval_schema_requires_provenance() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--schema", "schemas/retrieval_object.schema.json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_retrieval_object_missing_provenance_fails(tmp_path: Path) -> None:
    path = tmp_path / "bad_retrieval.jsonl"
    path.write_text(
        json.dumps(
            {
                "object_id": "obj1",
                "object_type": "semantic_chunk",
                "case_id": "CASE1",
                "company": "Example Co",
                "fiscal_period": "Q1 2026",
                "source_type": "manual_local",
                "source_ref": "manual://case1",
                "section": "prepared_remarks",
                "speaker": "",
                "topic": "",
                "span_hints": {},
                "evidence_text": "",
                "redacted_evidence_preview": "preview",
                "rights_tier": "manual_supplied",
                "raw_text_commit_allowed": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--path", str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "provenance" in result.stdout


def test_retrieval_helper_rejects_missing_provenance() -> None:
    row = {
        "object_id": "obj1",
        "object_type": "semantic_chunk",
        "case_id": "CASE1",
        "company": "Example Co",
        "fiscal_period": "Q1 2026",
        "source_type": "manual_local",
        "source_ref": "manual://case1",
        "section": "prepared_remarks",
        "speaker": "",
        "topic": "",
        "span_hints": {},
        "evidence_text": "",
        "redacted_evidence_preview": "preview",
        "rights_tier": "manual_supplied",
        "raw_text_commit_allowed": False,
        "deterministic_output_override_allowed": False,
    }

    errors = validate_retrieval_object(row)

    assert any("provenance" in error for error in errors)


def test_retrieval_helper_prioritizes_evidence_objects() -> None:
    assert retrieval_priority_for_type("evidence_object") == 1
    assert retrieval_priority_for_type("event_aligned_chunk") == 2
    assert retrieval_priority_for_type("semantic_chunk") == 3

    row = build_retrieval_object(
        object_id="ev1",
        object_type="evidence_object",
        case_id="CASE1",
        company="Example Co",
        fiscal_period="Q1 2026",
        source_type="manual_local",
        source_ref="manual://case1",
        section="qa",
        provenance={
            "source_path": "manual://case1",
            "span_ids": ["span-1"],
            "provenance_hash": "sha256:abc",
        },
        rights_tier="manual_supplied",
        raw_text_commit_allowed=False,
        redacted_evidence_preview="Management narrowed guidance.",
    )

    assert row["retrieval_priority"] == 1
    assert row["deterministic_output_override_allowed"] is False
