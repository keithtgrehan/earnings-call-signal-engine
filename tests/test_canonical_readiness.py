from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_canonical_readiness", ROOT / "scripts" / "build_canonical_readiness.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

build_canonical_readiness_summary = MODULE.build_canonical_readiness_summary
write_readiness_outputs = MODULE.write_readiness_outputs

LEGACY_BLOCKER_TERMS = (
    "legacy_gold_row_count",
    "legacy_gold_count",
    "legacy_rows_present",
    "blocked_gold_count",
    "blocked_provenance_rows",
    "repair_candidates",
    "repair",
    "legacy",
)


def _gold_row(label_id: str, *, provenance: bool = True) -> dict[str, object]:
    return {
        "case_id": "case_a",
        "label_id": label_id,
        "signal_type": "guidance_revision",
        "direction": "positive",
        "speaker_role": "management",
        "evidence_text": "We raised full-year revenue guidance.",
        "reviewer": "reviewer_1",
        "reviewed_at": "2026-01-01T00:00:00Z",
        "source_file": "registered/manual_local/case_a.txt",
        "provenance_hash": f"sha256:{label_id}" if provenance else "",
        "review_status": "reviewed",
    }


def _rows(*, strict_valid: int, legacy: int) -> list[dict[str, object]]:
    rows = [_gold_row(f"strict_{index:03d}") for index in range(strict_valid)]
    rows.extend(_gold_row(f"legacy_{index:03d}", provenance=False) for index in range(legacy))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def _assert_no_legacy_training_blockers(summary: dict[str, object]) -> None:
    blockers = " ".join(str(blocker) for blocker in summary["training_blockers"])
    for forbidden in LEGACY_BLOCKER_TERMS:
        assert forbidden not in blockers


def test_zero_strict_valid_with_legacy_rows_blocks_only_on_strict_count(tmp_path: Path) -> None:
    gold_path = tmp_path / "gold.jsonl"
    _write_jsonl(gold_path, _rows(strict_valid=0, legacy=57))

    summary = build_canonical_readiness_summary(gold_path=gold_path)

    assert summary["strict_valid_gold_count"] == 0
    assert summary["legacy_gold_count"] == 57
    assert summary["blocked_gold_count"] == 57
    assert summary["training_ready"] is False
    assert summary["training_status"] == "BLOCKED"
    assert summary["training_gate_reason"] == "strict_valid_gold_count_below_100"
    assert summary["training_blockers"] == ["strict_valid_gold_count_below_100"]
    assert summary["repair_findings"]["repair_candidates"] == 57
    assert summary["repair_findings"]["repair_required"] is True
    assert summary["canonical_gold_modified"] is False
    _assert_no_legacy_training_blockers(summary)


def test_ninety_nine_strict_valid_with_legacy_rows_still_blocks_on_strict_count(tmp_path: Path) -> None:
    gold_path = tmp_path / "gold.jsonl"
    _write_jsonl(gold_path, _rows(strict_valid=99, legacy=57))

    summary = build_canonical_readiness_summary(gold_path=gold_path)

    assert summary["strict_valid_gold_count"] == 99
    assert summary["legacy_gold_count"] == 57
    assert summary["training_ready"] is False
    assert summary["training_blockers"] == ["strict_valid_gold_count_below_100"]
    assert summary["repair_findings"]["repair_candidates"] == 57
    _assert_no_legacy_training_blockers(summary)


def test_one_hundred_strict_valid_with_legacy_rows_is_training_ready(tmp_path: Path) -> None:
    gold_path = tmp_path / "gold.jsonl"
    _write_jsonl(gold_path, _rows(strict_valid=100, legacy=57))

    summary = build_canonical_readiness_summary(gold_path=gold_path)

    assert summary["strict_valid_gold_count"] == 100
    assert summary["legacy_gold_count"] == 57
    assert summary["blocked_gold_count"] == 57
    assert summary["training_ready"] is True
    assert summary["training_status"] == "READY"
    assert summary["training_gate_reason"] == "strict_valid_gold_count_met_minimum"
    assert summary["training_blockers"] == []
    assert summary["repair_findings"]["repair_candidates"] == 57
    assert summary["training"]["training_allowed"] is True
    _assert_no_legacy_training_blockers(summary)


def test_readiness_outputs_are_machine_and_human_readable(tmp_path: Path) -> None:
    gold_path = tmp_path / "gold.jsonl"
    _write_jsonl(gold_path, _rows(strict_valid=1, legacy=0))
    summary = build_canonical_readiness_summary(gold_path=gold_path)
    json_out = tmp_path / "readiness.json"
    md_out = tmp_path / "readiness.md"

    write_readiness_outputs(summary, json_out=json_out, md_out=md_out)

    payload = json.loads(json_out.read_text(encoding="utf-8"))
    markdown = md_out.read_text(encoding="utf-8")
    assert payload["training_ready"] is False
    assert payload["training_blockers"] == ["strict_valid_gold_count_below_100"]
    assert "Strict-valid training gate" in markdown
    assert "Repair Findings" in markdown
    assert "No canonical gold rows were modified" in markdown


def test_build_canonical_readiness_cli_writes_requested_paths(tmp_path: Path) -> None:
    gold_path = tmp_path / "gold.jsonl"
    _write_jsonl(gold_path, _rows(strict_valid=1, legacy=0))
    json_out = tmp_path / "readiness.json"
    md_out = tmp_path / "readiness.md"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_canonical_readiness.py"),
            "--gold",
            str(gold_path),
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
    assert payload["minimum_strict_valid_gold_labels"] == 100


def test_training_readiness_report_uses_canonical_readiness_authority(tmp_path: Path) -> None:
    canonical_path = tmp_path / "readiness_canonical.json"
    json_out = tmp_path / "training_readiness.json"
    md_out = tmp_path / "training_readiness.md"
    canonical_payload = {
        "schema_version": "canonical_readiness.v1",
        "status": "NOT_READY",
        "training_ready": False,
        "training_status": "BLOCKED",
        "training_gate_reason": "strict_valid_gold_count_below_100",
        "training_blockers": ["strict_valid_gold_count_below_100"],
        "strict_valid_gold_count": 0,
        "minimum_strict_valid_gold_labels": 100,
        "legacy_gold_count": 57,
        "blocked_gold_count": 57,
        "repair_findings": {"repair_candidates": 57, "repair_required": True},
    }
    canonical_path.write_text(json.dumps(canonical_payload), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "report_training_readiness.py"),
            "--canonical-readiness",
            str(canonical_path),
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
    markdown = md_out.read_text(encoding="utf-8")
    assert payload["authoritative_source"] == str(canonical_path)
    assert payload["status"] == "NOT_READY"
    assert payload["training_ready"] is False
    assert payload["training_status"] == "BLOCKED"
    assert payload["training_attempted"] is False
    assert "Canonical readiness authority" in markdown
