from __future__ import annotations

import json
from pathlib import Path

from scripts.report_agent1_candidate_generation_readiness import build_readiness


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def test_no_registry_keeps_agent1_candidate_generation_not_ready(tmp_path: Path) -> None:
    registry = tmp_path / "missing.jsonl"

    readiness = build_readiness(registry_path=registry)

    assert readiness["state"] == "NOT_READY"
    assert readiness["manual_local_registry_exists"] is False
    assert readiness["can_generate_real_candidates"] is False
    assert "manual_local_registry.jsonl is missing" in readiness["missing_fields"]


def test_valid_registered_transcript_allows_agent1_candidate_generation(tmp_path: Path) -> None:
    source = tmp_path / "JPM_2026_Q1.txt"
    source.write_text("Operator: welcome\n", encoding="utf-8")
    registry = tmp_path / "manual_local_registry.jsonl"
    _write_jsonl(
        registry,
        [
            {
                "case_id": "jpm_2026_q1",
                "ticker": "JPM",
                "source_path_ref": str(source),
                "source_sha256": "sha256:abc",
                "media_type": "transcript",
                "source_type": "manual_local",
                "rights_tier": "manual_supplied",
                "operator_supplied": True,
                "registered_at": "2026-05-24T00:00:00+00:00",
                "raw_file_copied_into_repo": False,
                "commit_allowed": False,
                "training_allowed": False,
                "eval_allowed": False,
                "blocked_reason": "path/hash only",
                "provenance_hash": "sha256:registry",
            }
        ],
    )

    readiness = build_readiness(registry_path=registry)

    assert readiness["state"] == "READY_FOR_AGENT1_DETERMINISTIC_CANDIDATES"
    assert readiness["registered_transcript_count"] == 1
    assert readiness["valid_source_hash_count"] == 1
    assert readiness["eligible_case_count"] == 1
    assert readiness["can_generate_real_candidates"] is True
