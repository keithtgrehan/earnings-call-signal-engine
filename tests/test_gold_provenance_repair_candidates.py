from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.build_gold_provenance_repair_candidates import build_repair_candidates


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def test_registered_source_hash_creates_repair_candidate_without_editing_gold(tmp_path: Path) -> None:
    gold_path = tmp_path / "gold_labels.jsonl"
    registry_path = tmp_path / "manual_local_registry.jsonl"
    source_path = tmp_path / "JPM_2026_Q1.txt"
    source_path.write_text("Demand visibility is limited.\n", encoding="utf-8")
    source_sha = "sha256:" + hashlib.sha256(source_path.read_bytes()).hexdigest()
    gold_rows = [
        {
            "id": "g1",
            "candidate_id": "g1",
            "case_id": "jpm_2026_q1",
            "text": "Demand visibility is limited.",
            "signal_family": "uncertainty",
            "label_source": "normalized_import",
            "source_file": "legacy/JPM_2026_Q1.txt",
        }
    ]
    registry_rows = [
        {
            "case_id": "jpm_2026_q1",
            "source_path_ref": str(source_path),
            "source_sha256": source_sha,
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
    ]
    _write_jsonl(gold_path, gold_rows)
    _write_jsonl(registry_path, registry_rows)
    before = gold_path.read_bytes()

    candidates = build_repair_candidates(gold_path=gold_path, registry_path=registry_path, audit_dir=tmp_path / "missing")

    assert gold_path.read_bytes() == before
    assert candidates[0]["repair_status"] == "repairable_with_registered_source"
    assert candidates[0]["proposed_source_sha256"] == source_sha
    assert str(candidates[0]["proposed_provenance_hash"]).startswith("sha256:")
    assert candidates[0]["evidence_text"] == "Demand visibility is limited."
    assert candidates[0]["canonical_gold_edited"] is False


def test_repair_builder_does_not_invent_evidence_and_blocks_weak_external_rows(tmp_path: Path) -> None:
    gold_path = tmp_path / "gold_labels.jsonl"
    registry_path = tmp_path / "manual_local_registry.jsonl"
    rows = [
        {
            "id": "missing_evidence",
            "candidate_id": "missing_evidence",
            "case_id": "abc",
            "signal_family": "uncertainty",
            "label_source": "normalized_import",
            "source_file": "legacy/abc.txt",
        },
        {
            "id": "external",
            "candidate_id": "external",
            "case_id": "ext",
            "text": "Some benchmark text.",
            "signal_family": "uncertainty",
            "label_source": "external_dataset",
            "source_file": "external_dataset/foo.jsonl",
        },
        {
            "id": "dup_a",
            "candidate_id": "dup_a",
            "case_id": "dup",
            "text": "Repeated evidence.",
            "signal_family": "uncertainty",
            "label_source": "normalized_import",
            "source_file": "legacy/dup.txt",
        },
        {
            "id": "dup_b",
            "candidate_id": "dup_b",
            "case_id": "dup",
            "text": "Repeated evidence.",
            "signal_family": "uncertainty",
            "label_source": "normalized_import",
            "source_file": "legacy/dup.txt",
        },
    ]
    _write_jsonl(gold_path, rows)
    _write_jsonl(registry_path, [])

    candidates = build_repair_candidates(gold_path=gold_path, registry_path=registry_path, audit_dir=tmp_path / "missing")
    by_id = {str(row["candidate_id"]): row for row in candidates}

    assert by_id["missing_evidence"]["repair_status"] == "blocked_missing_evidence"
    assert by_id["missing_evidence"]["evidence_text"] == ""
    assert by_id["external"]["repair_status"] == "blocked_external_or_weak_source"
    assert by_id["dup_b"]["repair_status"] == "blocked_duplicate"
