from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

DEFAULT_READINESS_JSON = Path("reports/readiness_canonical.json")
DEFAULT_REPAIR_MANIFEST = Path("data/review/staging/legacy_gold_repair_manifest.jsonl")
DEFAULT_MINIMUM_STRICT_VALID_GOLD_LABELS = 100

STRICT_COUNT_BELOW_MINIMUM_BLOCKER = "strict_valid_gold_count_below_100"
CANONICAL_AUDIT_MISSING_BLOCKER = "canonical_gold_audit_missing"
CANONICAL_AUDIT_UNREADABLE_BLOCKER = "canonical_gold_audit_unreadable"
TRAINING_PLAN_MISSING_MINIMUM_BLOCKER = "training_plan_missing_minimum"
CONSISTENCY_MISMATCH_BLOCKER = "canonical_readiness_training_gate_mismatch"

ALLOWED_TRAINING_BLOCKERS = {
    STRICT_COUNT_BELOW_MINIMUM_BLOCKER,
    CANONICAL_AUDIT_MISSING_BLOCKER,
    CANONICAL_AUDIT_UNREADABLE_BLOCKER,
    TRAINING_PLAN_MISSING_MINIMUM_BLOCKER,
}
AVAILABILITY_BLOCKERS = {
    CANONICAL_AUDIT_MISSING_BLOCKER,
    CANONICAL_AUDIT_UNREADABLE_BLOCKER,
    TRAINING_PLAN_MISSING_MINIMUM_BLOCKER,
}

BLOCKED_OPERATIONS = {
    "model_training": "BLOCKED",
    "embeddings": "BLOCKED",
    "raw_transcript_download": "BLOCKED",
    "provider_api_calls": "BLOCKED",
    "canonical_gold_mutation": "BLOCKED",
}

BLOCKED_CLAIMS = {
    "alpha": "BLOCKED",
    "trading_performance": "BLOCKED",
    "causal_market_impact": "BLOCKED",
    "statistical_significance": "BLOCKED",
    "production_ml": "BLOCKED",
    "production_retrieval_quality": "BLOCKED",
}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _load_repair_manifest_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "repair_manifest_rows": 0,
            "repair_status_counts": {},
            "promotion_eligible_repair_rows": 0,
        }
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(payload)
    status_counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("repair_status", "unknown"))
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "path": str(path),
        "exists": True,
        "repair_manifest_rows": len(rows),
        "repair_status_counts": dict(sorted(status_counts.items())),
        "promotion_eligible_repair_rows": sum(1 for row in rows if row.get("promotion_eligible") is True),
    }


def _empty_repair_findings() -> dict[str, Any]:
    return {
        "legacy_gold_count": 0,
        "blocked_gold_count": 0,
        "repair_candidates": 0,
        "blocked_status_counts": {},
        "non_valid_status_counts": {},
        "parse_error_count": 0,
        "repair_required": False,
        "training_gate_impact": "none",
    }


def _missing_readiness(path: Path) -> dict[str, Any]:
    repair_findings = _empty_repair_findings()
    return {
        "schema_version": "canonical_readiness.v1",
        "status": "NOT_READY",
        "generated_at": datetime.now(UTC).isoformat(),
        "canonical_gold_modified": False,
        "canonical_truth_source": {
            "validator": "signal_engine.gold_review.audit_gold_labels",
            "gold_path": "data/gold/gold_labels.jsonl",
            "training_gate": "strict_valid_gold_count >= minimum_strict_valid_gold_labels",
        },
        "strict_valid_gold_count": 0,
        "legacy_gold_count": 0,
        "blocked_gold_count": 0,
        "minimum_strict_valid_gold_labels": DEFAULT_MINIMUM_STRICT_VALID_GOLD_LABELS,
        "training_ready": False,
        "training_status": "BLOCKED",
        "training_gate_reason": CANONICAL_AUDIT_MISSING_BLOCKER,
        "training_blockers": [CANONICAL_AUDIT_MISSING_BLOCKER],
        "repair_findings": repair_findings,
        "repair_status_counts": {},
        "gold": {
            "source_path": "data/gold/gold_labels.jsonl",
            "row_count": 0,
            "status_counts": {},
            "strict_valid_gold_count": 0,
            "strict_valid_adjudicated_label_count": 0,
            "legacy_gold_count": 0,
            "legacy_gold_row_count": 0,
            "legacy_repair_candidate_count": 0,
            "blocked_gold_count": 0,
            "training_ready_legacy_row_count": 0,
        },
        "training": {
            "status": "BLOCKED",
            "training_allowed": False,
            "training_ready": False,
            "minimum_strict_valid_gold_labels": DEFAULT_MINIMUM_STRICT_VALID_GOLD_LABELS,
            "min_strict_valid_adjudicated_labels": DEFAULT_MINIMUM_STRICT_VALID_GOLD_LABELS,
            "strict_valid_gold_count": 0,
            "strict_valid_adjudicated_label_count": 0,
            "missing_strict_valid_gold_labels": DEFAULT_MINIMUM_STRICT_VALID_GOLD_LABELS,
            "missing_strict_valid_adjudicated_labels": DEFAULT_MINIMUM_STRICT_VALID_GOLD_LABELS,
            "training_gate_reason": CANONICAL_AUDIT_MISSING_BLOCKER,
            "training_blockers": [CANONICAL_AUDIT_MISSING_BLOCKER],
            "blockers": [CANONICAL_AUDIT_MISSING_BLOCKER],
        },
        "policy": {
            "source_rights": {"status": "FAIL_CLOSED", "fail_closed": True, "summary": "Readiness report missing."},
            "provenance": {"status": "FAIL_CLOSED", "fail_closed": True, "summary": "Readiness report missing."},
            "artifact_policy": {"status": "FAIL_CLOSED", "fail_closed": True, "summary": "Readiness report missing."},
            "claim_safety": {"status": "FAIL_CLOSED", "fail_closed": True, "summary": "Readiness report missing."},
        },
        "blockers": [CANONICAL_AUDIT_MISSING_BLOCKER],
    }


def _training_blockers_from_readiness(readiness: dict[str, Any], training: dict[str, Any]) -> list[str]:
    raw_blockers = (
        readiness.get("training_blockers")
        or training.get("training_blockers")
        or training.get("blockers")
        or readiness.get("blockers")
        or []
    )
    blockers = [str(blocker) for blocker in raw_blockers if str(blocker).strip()]
    return [blocker for blocker in blockers if blocker in ALLOWED_TRAINING_BLOCKERS]


def _minimum_strict_valid_gold_labels(readiness: dict[str, Any], training: dict[str, Any]) -> int:
    return _safe_int(
        readiness.get("minimum_strict_valid_gold_labels")
        or readiness.get("minimum_required_strict_valid_gold_labels")
        or training.get("minimum_strict_valid_gold_labels")
        or training.get("min_strict_valid_adjudicated_labels"),
        DEFAULT_MINIMUM_STRICT_VALID_GOLD_LABELS,
    )


def _strict_valid_gold_count(readiness: dict[str, Any], training: dict[str, Any], gold: dict[str, Any]) -> int:
    return _safe_int(
        readiness.get("strict_valid_gold_count")
        or training.get("strict_valid_gold_count")
        or gold.get("strict_valid_gold_count"),
        0,
    )


def _computed_training_gate(
    *,
    readiness: dict[str, Any],
    training: dict[str, Any],
    strict_valid_gold_count: int,
    minimum_strict_valid_gold_labels: int,
) -> tuple[bool, str, list[str]]:
    readiness_blockers = _training_blockers_from_readiness(readiness, training)
    availability_blockers = [blocker for blocker in readiness_blockers if blocker in AVAILABILITY_BLOCKERS]
    if availability_blockers:
        return False, availability_blockers[0], availability_blockers
    if strict_valid_gold_count < minimum_strict_valid_gold_labels:
        return False, STRICT_COUNT_BELOW_MINIMUM_BLOCKER, [STRICT_COUNT_BELOW_MINIMUM_BLOCKER]
    return True, "strict_valid_gold_count_met_minimum", []


def _reported_consistency_errors(
    *,
    readiness: dict[str, Any],
    training: dict[str, Any],
    computed_ready: bool,
) -> list[str]:
    errors: list[str] = []
    expected_status = "READY" if computed_ready else "NOT_READY"
    expected_training_status = "READY" if computed_ready else "BLOCKED"
    reported_checks = [
        ("readiness.training_ready", readiness.get("training_ready")),
        ("training.training_ready", training.get("training_ready")),
        ("training.training_allowed", training.get("training_allowed")),
    ]
    for field, reported_value in reported_checks:
        if reported_value is not None and bool(reported_value) != computed_ready:
            errors.append(f"{field} disagrees with strict-valid gate")
    if readiness.get("status") in {"READY", "NOT_READY"} and readiness.get("status") != expected_status:
        errors.append("readiness.status disagrees with strict-valid gate")
    if training.get("status") in {"READY", "BLOCKED"} and training.get("status") != expected_training_status:
        errors.append("training.status disagrees with strict-valid gate")
    return errors


def _repair_findings_from_readiness(readiness: dict[str, Any], gold: dict[str, Any]) -> dict[str, Any]:
    findings = _empty_repair_findings()
    findings.update(dict(readiness.get("repair_findings") or {}))
    findings["legacy_gold_count"] = _safe_int(
        findings.get("legacy_gold_count")
        or readiness.get("legacy_gold_count")
        or gold.get("legacy_gold_count")
        or gold.get("legacy_gold_row_count")
        or gold.get("legacy_repair_candidate_count"),
        0,
    )
    findings["blocked_gold_count"] = _safe_int(
        findings.get("blocked_gold_count") or readiness.get("blocked_gold_count") or gold.get("blocked_gold_count"),
        0,
    )
    findings["repair_candidates"] = _safe_int(
        findings.get("repair_candidates") or gold.get("legacy_repair_candidate_count") or findings["legacy_gold_count"],
        0,
    )
    findings["repair_required"] = bool(
        findings.get("repair_required")
        or findings["legacy_gold_count"]
        or findings["blocked_gold_count"]
        or findings["repair_candidates"]
    )
    findings["training_gate_impact"] = "none"
    findings["blocked_status_counts"] = dict(findings.get("blocked_status_counts") or {})
    findings["non_valid_status_counts"] = dict(findings.get("non_valid_status_counts") or {})
    return findings


def build_control_room_status(
    *,
    readiness_json: Path = DEFAULT_READINESS_JSON,
    repair_manifest: Path = DEFAULT_REPAIR_MANIFEST,
) -> dict[str, Any]:
    readiness = _load_json(readiness_json)
    if not readiness:
        readiness = _missing_readiness(readiness_json)

    gold = dict(readiness.get("gold") or {})
    training = dict(readiness.get("training") or {})
    repair_manifest_summary = _load_repair_manifest_summary(repair_manifest)
    repair_findings = _repair_findings_from_readiness(readiness, gold)
    repair_status_counts = dict(repair_manifest_summary["repair_status_counts"])
    if repair_status_counts:
        repair_findings["repair_status_counts"] = repair_status_counts

    minimum_strict_valid_gold_labels = _minimum_strict_valid_gold_labels(readiness, training)
    strict_valid_gold_count = _strict_valid_gold_count(readiness, training, gold)
    computed_ready, training_gate_reason, training_blockers = _computed_training_gate(
        readiness=readiness,
        training=training,
        strict_valid_gold_count=strict_valid_gold_count,
        minimum_strict_valid_gold_labels=minimum_strict_valid_gold_labels,
    )
    consistency_errors = _reported_consistency_errors(
        readiness=readiness,
        training=training,
        computed_ready=computed_ready,
    )
    training_ready = computed_ready and not consistency_errors
    if consistency_errors and CONSISTENCY_MISMATCH_BLOCKER not in training_blockers:
        training_blockers = [*training_blockers, CONSISTENCY_MISMATCH_BLOCKER]
    training_status = "READY" if training_ready else "BLOCKED"
    status = "READY" if training_ready else "NOT_READY"

    reports = [
        {
            "id": "canonical_readiness",
            "path": str(readiness_json),
            "exists": readiness_json.exists(),
            "status": str(readiness.get("status", "NOT_READY")),
        },
        {
            "id": "gold_label_audit",
            "path": "reports/gold_label_audit/gold_label_audit.json",
            "exists": Path("reports/gold_label_audit/gold_label_audit.json").exists(),
            "status": "REFERENCE",
        },
        {
            "id": "legacy_gold_repair_manifest",
            "path": str(repair_manifest),
            "exists": repair_manifest.exists(),
            "status": "REFERENCE" if repair_manifest.exists() else "MISSING",
        },
        {
            "id": "training_readiness",
            "path": "reports/training_readiness.json",
            "exists": Path("reports/training_readiness.json").exists(),
            "status": "REFERENCE",
        },
    ]
    next_actions = list(
        readiness.get("next_actions")
        or [
            "Run canonical readiness after gold audit refresh.",
            "Repair/adjudicate labels through promotion manifests before training.",
        ]
    )
    if repair_manifest_summary["repair_manifest_rows"]:
        next_actions.insert(
            0,
            f"Work the legacy repair manifest at {repair_manifest_summary['path']} before preparing any promotion manifest.",
        )

    return {
        "schema_version": "control_room_status.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": status,
        "summary": (
            "Training blocked until strict-valid gold rows reach "
            f"{minimum_strict_valid_gold_labels}."
            if not training_ready
            else "Training readiness gate is satisfied; execution still requires an explicit separate training command."
        ),
        "strict_valid_gold_count": strict_valid_gold_count,
        "minimum_strict_valid_gold_labels": minimum_strict_valid_gold_labels,
        "training_ready": training_ready,
        "training_status": training_status,
        "training_gate_reason": training_gate_reason,
        "training_blockers": training_blockers,
        "repair_findings": repair_findings,
        "repair_status_counts": repair_status_counts,
        "consistency_errors": consistency_errors,
        "canonical_truth_source": readiness.get("canonical_truth_source")
        or {
            "validator": "signal_engine.gold_review.audit_gold_labels",
            "gold_path": gold.get("source_path", "data/gold/gold_labels.jsonl"),
            "training_gate": "strict_valid_gold_count >= minimum_strict_valid_gold_labels",
        },
        "gold": {
            "source_path": gold.get("source_path", "data/gold/gold_labels.jsonl"),
            "row_count": _safe_int(gold.get("row_count"), 0),
            "status_counts": dict(gold.get("status_counts") or {}),
            "strict_valid_gold_count": strict_valid_gold_count,
            "strict_valid_adjudicated_label_count": _safe_int(
                gold.get("strict_valid_adjudicated_label_count")
                or training.get("strict_valid_adjudicated_label_count"),
                0,
            ),
            "legacy_gold_count": _safe_int(gold.get("legacy_gold_count") or repair_findings["legacy_gold_count"], 0),
            "legacy_gold_row_count": _safe_int(gold.get("legacy_gold_row_count") or repair_findings["legacy_gold_count"], 0),
            "legacy_repair_candidate_count": _safe_int(
                gold.get("legacy_repair_candidate_count") or repair_findings["repair_candidates"],
                0,
            ),
            "blocked_gold_count": _safe_int(gold.get("blocked_gold_count") or repair_findings["blocked_gold_count"], 0),
            "training_ready_legacy_row_count": _safe_int(gold.get("training_ready_legacy_row_count"), 0),
        },
        "training": {
            "status": training_status,
            "training_allowed": training_ready,
            "training_ready": training_ready,
            "minimum_strict_valid_gold_labels": minimum_strict_valid_gold_labels,
            "min_strict_valid_adjudicated_labels": minimum_strict_valid_gold_labels,
            "strict_valid_gold_count": strict_valid_gold_count,
            "strict_valid_adjudicated_label_count": _safe_int(training.get("strict_valid_adjudicated_label_count"), 0),
            "missing_strict_valid_gold_labels": max(minimum_strict_valid_gold_labels - strict_valid_gold_count, 0),
            "missing_strict_valid_adjudicated_labels": max(
                minimum_strict_valid_gold_labels - strict_valid_gold_count,
                0,
            ),
            "training_gate_reason": training_gate_reason,
            "training_blockers": training_blockers,
            "blockers": training_blockers,
            "consistency_errors": consistency_errors,
        },
        "policy": dict(readiness.get("policy") or {}),
        "repair_manifest": repair_manifest_summary,
        "operations": dict(BLOCKED_OPERATIONS),
        "claims": dict(BLOCKED_CLAIMS),
        "reports": reports,
        "next_actions": next_actions,
        "execution_notes": [
            "No training was run.",
            "No embeddings were created.",
            "No transcripts, audio, video, or slides were downloaded.",
            "No provider APIs were called.",
            "Canonical gold data was not mutated.",
        ],
    }


def write_control_room_outputs(status: dict[str, Any], *, json_out: Path, md_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    gold = status["gold"]
    training = status["training"]
    repair_findings = status["repair_findings"]
    lines = [
        "# Control Room Status",
        "",
        "This status is generated from canonical readiness and existing validation reports. It does not execute training, retrieval, downloads, or provider calls.",
        "",
        f"- Status: `{status['status']}`",
        f"- Training: `{training['status']}`",
        f"- Training ready: `{status['training_ready']}`",
        f"- Strict-valid gold rows: `{status['strict_valid_gold_count']}` / `{status['minimum_strict_valid_gold_labels']}`",
        f"- Strict-valid adjudicated labels (informational): `{training['strict_valid_adjudicated_label_count']}`",
        f"- Legacy repair candidate rows: `{gold['legacy_repair_candidate_count']}`",
        f"- Legacy repair manifest rows: `{status['repair_manifest']['repair_manifest_rows']}`",
        f"- Promotion-eligible repair rows: `{status['repair_manifest']['promotion_eligible_repair_rows']}`",
        f"- Training gate reason: `{status['training_gate_reason']}`",
        "",
        "No provider APIs were called. No canonical gold rows were modified.",
        "",
        "## Training Blockers",
        "",
    ]
    lines.extend(f"- `{blocker}`" for blocker in status["training_blockers"] or ["none"])
    lines.extend(["", "## Repair Findings", ""])
    lines.extend(
        [
            f"- Legacy gold rows: `{repair_findings.get('legacy_gold_count', 0)}`",
            f"- Blocked gold rows: `{repair_findings.get('blocked_gold_count', 0)}`",
            f"- Repair candidates: `{repair_findings.get('repair_candidates', 0)}`",
            f"- Repair required: `{repair_findings.get('repair_required', False)}`",
            "- Training gate impact: `none`",
        ]
    )
    lines.extend(["", "## Repair Manifest", ""])
    for repair_status, count in status["repair_manifest"]["repair_status_counts"].items():
        lines.append(f"- `{repair_status}`: `{count}`")
    if not status["repair_manifest"]["repair_status_counts"]:
        lines.append("- none")
    if status["consistency_errors"]:
        lines.extend(["", "## Consistency Errors", ""])
        lines.extend(f"- {error}" for error in status["consistency_errors"])
    lines.extend([
        "",
        "## Blocked Operations",
        "",
    ])
    lines.extend(f"- `{name}`: `{value}`" for name, value in sorted(status["operations"].items()))
    lines.extend(["", "## Blocked Claims", ""])
    lines.extend(f"- `{name}`: `{value}`" for name, value in sorted(status["claims"].items()))
    lines.extend(["", "## Reports", ""])
    for report in status["reports"]:
        lines.append(f"- `{report['id']}`: `{report['path']}` exists=`{report['exists']}` status=`{report['status']}`")
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {action}" for action in status["next_actions"])
    md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
