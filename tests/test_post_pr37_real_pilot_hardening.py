from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from signal_engine.agent5_acquisition import decide_source_use
from signal_engine.artifacts.manifest import build_artifact_manifest, validate_artifact_manifest
from signal_engine.evaluation.claim_gates import validate_claim_language
from signal_engine.evaluation.sample_gates import evaluate_sample_gates
from signal_engine.gold_review import validate_promotion_rows
from signal_engine.labels import LabelState
from signal_engine.manual_local_discovery import discover_manual_local_paths

ROOT = Path(__file__).resolve().parents[1]


def test_signal_engine_cli_alias_and_doctor_json() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'signal-engine = "earnings_call_sentiment.cli:main"' in pyproject

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    proc = subprocess.run(
        [sys.executable, "-m", "earnings_call_sentiment", "doctor", "--json"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["status"] in {"ok", "warning"}
    assert payload["provider_credentials_required"] is False
    assert "package_import" in payload["checks"]
    assert payload["checks"]["reports_writable"]["status"] == "ok"


def test_artifact_manifest_contract_and_hashes(tmp_path: Path) -> None:
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "report.md"
    input_file.write_text('{"ok": true}\n', encoding="utf-8")
    output_file.write_text("# Report\n", encoding="utf-8")

    manifest = build_artifact_manifest(
        run_id="run_001",
        command="pytest",
        inputs=[input_file],
        outputs=[output_file],
        config_paths=[input_file],
        schema_versions={"artifact_manifest": "1.0.0"},
        generated_by="pytest",
        deterministic_core_version="agent1_rules_v1",
    )

    assert not validate_artifact_manifest(manifest)
    assert manifest["input_hashes"][str(input_file)].startswith("sha256:")
    assert manifest["output_hashes"][str(output_file)].startswith("sha256:")
    broken = dict(manifest)
    broken.pop("run_id")
    assert validate_artifact_manifest(broken)


def test_label_states_and_strict_promotion_validator() -> None:
    assert LabelState.ACCEPTED_GOLD.value == "accepted_gold"
    errors = validate_promotion_rows(
        [
            {
                "label_id": "l1",
                "case_id": "c1",
                "final_label": "uncertainty",
                "suggested_label": "uncertainty",
                "review_status": "reviewed",
                "gold_status": "promotion_candidate",
                "reviewer": "human",
                "reviewed_at": "2026-01-01",
                "evidence_text": "Demand visibility is limited.",
                "source_file": "manual://x",
                "provenance_hash": "sha256:abc",
                "contamination_flags": [],
            }
        ]
    )
    assert any("review_status must be adjudicated" in error for error in errors)
    assert any("adjudicator" in error for error in errors)
    assert any("reviewer rationale" in error for error in errors)


def test_source_rights_decision_engine_fail_closed() -> None:
    assert decide_source_use({"source_type": "official_ir_transcript"})["decision"] == "blocked"
    assert decide_source_use({"source_type": "youtube_metadata_only", "raw_video_allowed": True})["decision"] == "blocked"
    assert decide_source_use({"source_type": "sec_edgar_metadata", "raw_body_allowed": False})["decision"] == "metadata_only"
    allowed = decide_source_use(
        {
            "source_type": "official_ir_transcript",
            "rights_tier": "official_ir_allowed",
            "terms_checked": True,
            "robots_checked": True,
            "allowed_storage": True,
            "commit_allowed": False,
            "eval_allowed": True,
            "raw_body_allowed": True,
        }
    )
    assert allowed["decision"] == "allowed"
    assert allowed["asset_availability"]["transcript_availability"]["status"] == "available_raw_allowed"


def test_evaluation_gate_and_claim_language_are_guarded() -> None:
    thirty = evaluate_sample_gates(valid_gold_count=0, call_count=30)
    assert thirty["pilot_30_call"]["status"] == "PIPELINE_READY_ONLY"
    assert thirty["signal_eval"]["status"] == "NOT_ENOUGH_DATA"
    hundred = evaluate_sample_gates(valid_gold_count=100, call_count=120)
    assert hundred["signal_eval"]["status"] == "READY"
    errors = validate_claim_language("This proves alpha and statistically significant trading performance.")
    assert "NO_TRADING_CLAIM" in errors
    assert "NO_SIGNIFICANCE_CLAIM" in errors


def test_manual_local_discovery_is_metadata_only_and_directory_gated(tmp_path: Path) -> None:
    approved = tmp_path / "approved"
    blocked = tmp_path / "blocked"
    approved.mkdir()
    blocked.mkdir()
    transcript = approved / "ABC_2025_Q4.txt"
    transcript.write_text("Operator: welcome\n", encoding="utf-8")
    outside = blocked / "XYZ_2025_Q4.txt"
    outside.write_text("Operator: welcome\n", encoding="utf-8")

    rows = discover_manual_local_paths(
        search_dirs=[approved, blocked],
        approved_dirs=[approved],
        allowed_extensions={".txt"},
        source_kind="transcript",
    )

    by_path = {Path(str(row["path_ref"])).name: row for row in rows}
    assert by_path["ABC_2025_Q4.txt"]["status"] == "candidate_metadata_only"
    assert by_path["ABC_2025_Q4.txt"]["sha256"].startswith("sha256:")
    assert by_path["ABC_2025_Q4.txt"]["raw_file_copied_into_repo"] is False
    assert by_path["XYZ_2025_Q4.txt"]["status"] == "blocked_outside_approved_directories"
