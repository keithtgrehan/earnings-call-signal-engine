from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.control_room.status import build_control_room_status, write_control_room_outputs


def _readiness_payload(
    *,
    strict_valid_gold_count: int = 0,
    legacy_gold_count: int = 57,
    training_ready: bool | None = None,
) -> dict[str, object]:
    if training_ready is None:
        training_ready = strict_valid_gold_count >= 100
    training_status = "READY" if training_ready else "BLOCKED"
    status = "READY" if training_ready else "NOT_READY"
    blockers = [] if training_ready else ["strict_valid_gold_count_below_100"]
    gate_reason = "strict_valid_gold_count_met_minimum" if training_ready else "strict_valid_gold_count_below_100"
    return {
        "schema_version": "canonical_readiness.v1",
        "status": status,
        "generated_at": "2026-01-01T00:00:00+00:00",
        "canonical_gold_modified": False,
        "canonical_truth_source": {
            "validator": "signal_engine.gold_review.audit_gold_labels",
            "gold_path": "data/gold/gold_labels.jsonl",
            "training_gate": "strict_valid_gold_count >= minimum_strict_valid_gold_labels",
        },
        "strict_valid_gold_count": strict_valid_gold_count,
        "legacy_gold_count": legacy_gold_count,
        "blocked_gold_count": legacy_gold_count,
        "minimum_strict_valid_gold_labels": 100,
        "training_ready": training_ready,
        "training_status": training_status,
        "training_gate_reason": gate_reason,
        "training_blockers": blockers,
        "repair_findings": {
            "legacy_gold_count": legacy_gold_count,
            "blocked_gold_count": legacy_gold_count,
            "repair_candidates": legacy_gold_count,
            "blocked_status_counts": {"BLOCKED_NO_PROVENANCE": legacy_gold_count} if legacy_gold_count else {},
            "repair_required": bool(legacy_gold_count),
            "training_gate_impact": "none",
        },
        "repair_status_counts": {},
        "gold": {
            "source_path": "data/gold/gold_labels.jsonl",
            "row_count": strict_valid_gold_count + legacy_gold_count,
            "status_counts": {"BLOCKED_NO_PROVENANCE": legacy_gold_count} if legacy_gold_count else {},
            "strict_valid_gold_count": strict_valid_gold_count,
            "strict_valid_adjudicated_label_count": 0,
            "legacy_gold_count": legacy_gold_count,
            "legacy_gold_row_count": legacy_gold_count,
            "legacy_repair_candidate_count": legacy_gold_count,
            "blocked_gold_count": legacy_gold_count,
            "training_ready_legacy_row_count": 0,
        },
        "training": {
            "status": training_status,
            "training_allowed": training_ready,
            "training_ready": training_ready,
            "minimum_strict_valid_gold_labels": 100,
            "min_strict_valid_adjudicated_labels": 100,
            "strict_valid_gold_count": strict_valid_gold_count,
            "strict_valid_adjudicated_label_count": 0,
            "missing_strict_valid_gold_labels": max(100 - strict_valid_gold_count, 0),
            "missing_strict_valid_adjudicated_labels": max(100 - strict_valid_gold_count, 0),
            "training_gate_reason": gate_reason,
            "training_blockers": blockers,
            "blockers": blockers,
        },
        "policy": {
            "source_rights": {"status": "FAIL_CLOSED"},
            "provenance": {"status": "FAIL_CLOSED"},
            "artifact_policy": {"status": "PASS"},
            "claim_safety": {"status": "PASS"},
        },
        "blockers": blockers,
    }


def test_control_room_status_blocks_training_and_unsafe_operations(tmp_path: Path) -> None:
    readiness_path = tmp_path / "readiness_canonical.json"
    readiness_path.write_text(json.dumps(_readiness_payload()), encoding="utf-8")

    status = build_control_room_status(
        readiness_json=readiness_path,
        repair_manifest=tmp_path / "missing_repair_manifest.jsonl",
    )

    assert status["status"] == "NOT_READY"
    assert status["training"]["status"] == "BLOCKED"
    assert status["training"]["training_allowed"] is False
    assert status["strict_valid_gold_count"] == 0
    assert status["minimum_strict_valid_gold_labels"] == 100
    assert status["training_gate_reason"] == "strict_valid_gold_count_below_100"
    assert status["training_blockers"] == ["strict_valid_gold_count_below_100"]
    assert status["repair_findings"]["repair_candidates"] == 57
    assert status["gold"]["legacy_repair_candidate_count"] == 57
    assert status["operations"]["model_training"] == "BLOCKED"
    assert status["operations"]["embeddings"] == "BLOCKED"
    assert status["operations"]["raw_transcript_download"] == "BLOCKED"
    assert status["operations"]["provider_api_calls"] == "BLOCKED"
    assert status["operations"]["canonical_gold_mutation"] == "BLOCKED"
    assert status["claims"]["alpha"] == "BLOCKED"
    assert status["claims"]["production_ml"] == "BLOCKED"


def test_control_room_ready_state_follows_strict_valid_gate_not_legacy_rows(tmp_path: Path) -> None:
    readiness_path = tmp_path / "readiness_canonical.json"
    readiness_path.write_text(
        json.dumps(_readiness_payload(strict_valid_gold_count=100, legacy_gold_count=57)),
        encoding="utf-8",
    )

    status = build_control_room_status(
        readiness_json=readiness_path,
        repair_manifest=tmp_path / "missing_repair_manifest.jsonl",
    )

    assert status["status"] == "READY"
    assert status["training"]["status"] == "READY"
    assert status["training_ready"] is True
    assert status["training_blockers"] == []
    assert status["repair_findings"]["repair_candidates"] == 57
    assert status["repair_findings"]["training_gate_impact"] == "none"


def test_control_room_consistency_mismatch_fails_closed(tmp_path: Path) -> None:
    readiness_path = tmp_path / "readiness_canonical.json"
    payload = _readiness_payload(strict_valid_gold_count=0, legacy_gold_count=57, training_ready=True)
    readiness_path.write_text(json.dumps(payload), encoding="utf-8")

    status = build_control_room_status(
        readiness_json=readiness_path,
        repair_manifest=tmp_path / "missing_repair_manifest.jsonl",
    )

    assert status["status"] == "NOT_READY"
    assert status["training_ready"] is False
    assert status["training"]["status"] == "BLOCKED"
    assert "strict_valid_gold_count_below_100" in status["training_blockers"]
    assert "canonical_readiness_training_gate_mismatch" in status["training_blockers"]
    assert status["consistency_errors"]


def test_control_room_outputs_and_schema_contract(tmp_path: Path) -> None:
    readiness_path = tmp_path / "readiness_canonical.json"
    readiness_path.write_text(json.dumps(_readiness_payload()), encoding="utf-8")
    status = build_control_room_status(
        readiness_json=readiness_path,
        repair_manifest=tmp_path / "missing_repair_manifest.jsonl",
    )
    json_out = tmp_path / "status.json"
    md_out = tmp_path / "status.md"

    write_control_room_outputs(status, json_out=json_out, md_out=md_out)

    payload = json.loads(json_out.read_text(encoding="utf-8"))
    markdown = md_out.read_text(encoding="utf-8")
    schema = json.loads((ROOT / "schemas" / "control_room_status.schema.json").read_text(encoding="utf-8"))

    assert payload["schema_version"] == "control_room_status.v1"
    assert payload["strict_valid_gold_count"] == 0
    assert payload["repair_findings"]["repair_candidates"] == 57
    assert "Training: `BLOCKED`" in markdown
    assert "Strict-valid gold rows" in markdown
    assert "No provider APIs were called" in markdown
    assert "schema_version" in schema["required"]
    assert "repair_findings" in schema["required"]
    assert "operations" in schema["required"]
    assert schema["properties"]["claims"]["additionalProperties"]["enum"] == ["BLOCKED"]


def test_build_control_room_status_cli_writes_requested_paths(tmp_path: Path) -> None:
    readiness_path = tmp_path / "readiness_canonical.json"
    readiness_path.write_text(json.dumps(_readiness_payload()), encoding="utf-8")
    json_out = tmp_path / "status.json"
    md_out = tmp_path / "status.md"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_control_room_status.py"),
            "--readiness-json",
            str(readiness_path),
            "--repair-manifest",
            str(tmp_path / "missing_repair_manifest.jsonl"),
            "--json-out",
            str(json_out),
            "--md-out",
            str(md_out),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["status"] == "NOT_READY"
    assert payload["reports"][0]["path"] == str(readiness_path)


def test_control_room_make_targets_are_present_without_repair_manifest_mutation() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    for target in ("readiness-canonical", "control-room-status", "training-control-room-check"):
        assert f"{target}:" in makefile
    assert "control-room-status: readiness-canonical legacy-gold-repair" not in makefile
