from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "multimodal_audit_output.schema.json"


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def valid_payload() -> dict:
    return {
        "record_id": "audit-window-001",
        "source_type": "multimodal_audit",
        "canonical_status": "reviewer_support_only",
        "transcript_window_ref": "call-001:qa:120.0-150.0",
        "features": {
            "pause_duration": 1.2,
            "asr_confidence": 0.92,
            "head_pose_metadata": {"yaw_summary": "metadata_only"},
        },
        "confidence": 0.81,
        "provenance": {
            "source_rights_record_id": "rights-cleared-local-001",
            "extractor_name": "metadata-placeholder",
            "extractor_version": "0.0",
            "run_timestamp": "2026-05-23T00:00:00Z",
            "rights_cleared": True,
        },
        "interpretation_limits": [
            "does_not_infer_true_emotion",
            "does_not_detect_deception",
            "does_not_score_personality",
            "not_canonical_signal",
        ],
        "reviewer_note": "Observable cue metadata for reviewer support only.",
    }


def schema_errors(payload: dict) -> list[str]:
    schema = load_schema()
    errors: list[str] = []

    for field in schema["required"]:
        if field not in payload:
            errors.append(f"missing required field: {field}")

    allowed = set(schema["properties"])
    for field in payload:
        if field not in allowed:
            errors.append(f"additional property forbidden: {field}")

    if payload.get("canonical_status") != schema["properties"]["canonical_status"]["const"]:
        errors.append("canonical_status must equal reviewer_support_only")

    if payload.get("source_type") not in schema["properties"]["source_type"]["enum"]:
        errors.append("source_type enum violation")

    provenance = payload.get("provenance")
    if isinstance(provenance, dict):
        provenance_schema = schema["properties"]["provenance"]
        for field in provenance_schema["required"]:
            if field not in provenance:
                errors.append(f"missing provenance field: {field}")
        if provenance.get("rights_cleared") is not True:
            errors.append("provenance rights_cleared must be true")
    elif "provenance" in payload:
        errors.append("provenance must be an object")

    limits = set(payload.get("interpretation_limits", []))
    required_limits = {
        "does_not_infer_true_emotion",
        "does_not_detect_deception",
        "does_not_score_personality",
        "not_canonical_signal",
    }
    for limit in required_limits:
        if limit not in limits:
            errors.append(f"missing interpretation limit: {limit}")

    banned = [
        required[0]
        for rule in schema["not"]["anyOf"]
        for required in [rule["required"]]
    ]
    for field in banned:
        if field in payload:
            errors.append(f"banned field present: {field}")

    return errors


def test_valid_reviewer_support_output_passes() -> None:
    assert schema_errors(valid_payload()) == []


@pytest.mark.parametrize(
    "field",
    [
        "emotion_label",
        "deception_score",
        "manipulation_score",
        "biometric_identity",
    ],
)
def test_banned_fields_fail(field: str) -> None:
    payload = valid_payload()
    payload[field] = "blocked"

    assert schema_errors(payload)


def test_canonical_status_must_be_reviewer_support_only() -> None:
    payload = valid_payload()
    payload["canonical_status"] = "canonical_signal"

    assert "canonical_status must equal reviewer_support_only" in schema_errors(payload)


def test_missing_provenance_fails() -> None:
    payload = copy.deepcopy(valid_payload())
    payload.pop("provenance")

    assert "missing required field: provenance" in schema_errors(payload)
