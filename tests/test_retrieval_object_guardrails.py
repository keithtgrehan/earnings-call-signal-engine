from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

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
