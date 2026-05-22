from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

REQUIRED_TRAINING_PLAN_FIELDS = {
    "task_name",
    "task_type",
    "allowed_sources",
    "forbidden_sources",
    "gold_label_path",
    "rights_registry_path",
    "min_gold_labels",
    "min_reviewers",
    "label_schema_version",
    "external_datasets_allowed",
    "external_datasets_mode",
    "output_artifact_policy",
    "model_family",
    "training_enabled",
    "reason_if_disabled",
    "evaluation_metrics",
    "leakage_checks",
    "claim_limits",
}

MODEL_FAMILIES = {"sklearn_baseline", "transformer_candidate", "llm_reviewer"}
FORBIDDEN_GOLD_SOURCE_KINDS = {"weak_labels", "external_benchmark_rows", "external_dataset", "retrieval_only_records"}
FORBIDDEN_CLAIM_LIMITS = {
    "no_alpha",
    "no_trading_performance",
    "no_live_execution",
    "no_production_ml_claim",
    "no_statistical_significance_claim",
}


def validate_training_plan_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in sorted(REQUIRED_TRAINING_PLAN_FIELDS - set(payload)):
        errors.append(f"missing required field {field}")
    if payload.get("external_datasets_allowed") is not False:
        errors.append("external_datasets_allowed must be false by default")
    if payload.get("external_datasets_mode") != "benchmark_only":
        errors.append("external_datasets_mode must be benchmark_only")
    if payload.get("output_artifact_policy") != "no_model_weights_committed":
        errors.append("output_artifact_policy must be no_model_weights_committed")
    if payload.get("output_path_policy", "tmp_only") != "tmp_only":
        errors.append("output_path_policy must be tmp_only")
    if payload.get("model_family") not in MODEL_FAMILIES:
        errors.append(f"model_family must be one of {sorted(MODEL_FAMILIES)}")
    if payload.get("model_family") == "llm_reviewer" and payload.get("canonical_output_allowed") is not False:
        errors.append("llm_reviewer cannot be canonical output")
    if payload.get("canonical_output_allowed", False) is not False:
        errors.append("canonical_output_allowed must be false")
    if payload.get("llm_reviewer_canonical_allowed", False) is not False:
        errors.append("llm_reviewer_canonical_allowed must be false")
    dependency_policy = payload.get("dependency_policy") or {}
    if dependency_policy and dependency_policy.get("new_dependencies_allowed") is not False:
        errors.append("dependency_policy.new_dependencies_allowed must be false")
    database_policy = payload.get("database_policy") or {}
    if database_policy and database_policy.get("managed_databases") != "blocked":
        errors.append("database_policy.managed_databases must be blocked")
    training_data_inventory = payload.get("training_data_inventory") or {}
    if training_data_inventory and training_data_inventory.get("external_datasets_mode") != "benchmark_only":
        errors.append("training_data_inventory.external_datasets_mode must be benchmark_only")
    if payload.get("training_enabled") is True and not payload.get("allowed_sources"):
        errors.append("training_enabled cannot be true without explicit allowed_sources")
    if payload.get("training_enabled") is False and not str(payload.get("reason_if_disabled", "")).strip():
        errors.append("reason_if_disabled is required when training is disabled")
    try:
        if int(payload.get("min_gold_labels", 0)) <= 0:
            errors.append("min_gold_labels must be positive")
    except (TypeError, ValueError):
        errors.append("min_gold_labels must be an integer")
    try:
        if int(payload.get("min_reviewers", 0)) <= 0:
            errors.append("min_reviewers must be positive")
    except (TypeError, ValueError):
        errors.append("min_reviewers must be an integer")
    claim_limits = set(payload.get("claim_limits") or [])
    for claim_limit in sorted(FORBIDDEN_CLAIM_LIMITS - claim_limits):
        errors.append(f"claim_limits missing {claim_limit}")
    for index, source in enumerate(payload.get("allowed_sources") or [], start=1):
        if isinstance(source, str):
            source_kind = source
            rights_tier = ""
            training_allowed = False
        elif isinstance(source, dict):
            source_kind = str(source.get("source_kind") or source.get("source_type") or source.get("source_id") or "")
            rights_tier = str(source.get("rights_tier", ""))
            training_allowed = source.get("training_allowed") is True
        else:
            errors.append(f"allowed_sources[{index}] must be a string or object")
            continue
        if source_kind in FORBIDDEN_GOLD_SOURCE_KINDS:
            errors.append(f"allowed_sources[{index}] cannot use {source_kind} as gold")
        if rights_tier in {"unknown", "restricted"}:
            errors.append(f"allowed_sources[{index}] has blocked rights_tier {rights_tier}")
        if payload.get("training_enabled") is True and not training_allowed:
            errors.append(f"allowed_sources[{index}] must explicitly allow training when training_enabled is true")
    return errors


def build_training_readiness_summary(
    *,
    payload: dict[str, Any],
    gold_summary: dict[str, Any],
    rights_errors: list[str],
) -> dict[str, Any]:
    plan_errors = validate_training_plan_payload(payload)
    readiness_blockers: list[str] = []
    if gold_summary.get("status") != "valid":
        readiness_blockers.append("gold labels do not pass validation")
    row_count = int(gold_summary.get("row_count") or 0)
    min_gold_labels = int(payload.get("min_gold_labels") or 0)
    if row_count < min_gold_labels:
        readiness_blockers.append(f"gold label count {row_count} is below min_gold_labels {min_gold_labels}")
    if rights_errors:
        readiness_blockers.append("rights registry does not pass validation")
    if payload.get("training_enabled") is not True:
        readiness_blockers.append("training_enabled is false")
    if payload.get("external_datasets_allowed") is not False:
        readiness_blockers.append("external datasets are not allowed for training by default")
    status = "invalid" if plan_errors else "ready" if not readiness_blockers else "not_ready"
    return {
        "status": status,
        "task_name": payload.get("task_name", ""),
        "training_enabled": payload.get("training_enabled") is True,
        "gold_label_path": payload.get("gold_label_path", ""),
        "gold_label_count": row_count,
        "min_gold_labels": min_gold_labels,
        "plan_errors": plan_errors,
        "readiness_blockers": readiness_blockers,
        "rights_errors": rights_errors,
        "output_artifact_policy": payload.get("output_artifact_policy", ""),
        "model_family": payload.get("model_family", ""),
    }


def synthetic_smoke_examples() -> list[dict[str, str]]:
    return [
        {"text": "management raised guidance and reiterated demand strength", "label": "opportunity_commitment"},
        {"text": "we will expand capacity and follow up next quarter", "label": "opportunity_commitment"},
        {"text": "visibility remains limited and timing may move", "label": "uncertainty"},
        {"text": "the outlook depends on macro demand and supply timing", "label": "uncertainty"},
        {"text": "analysts pressed management on margin pressure", "label": "risk_friction"},
        {"text": "the customer dispute remains unresolved and could escalate", "label": "risk_friction"},
        {"text": "the operator introduced the prepared remarks", "label": "neutral"},
        {"text": "the call moved from prepared remarks to questions", "label": "neutral"},
    ]


def _predict_label(text: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in ("raised guidance", "expand", "follow up", "strength")):
        return "opportunity_commitment"
    if any(term in lowered for term in ("limited", "depends", "may", "timing")):
        return "uncertainty"
    if any(term in lowered for term in ("pressed", "pressure", "dispute", "unresolved", "escalate")):
        return "risk_friction"
    return "neutral"


def synthetic_smoke_metrics(rows: list[dict[str, str]] | None = None) -> dict[str, Any]:
    examples = rows or synthetic_smoke_examples()
    predictions = [_predict_label(row["text"]) for row in examples]
    labels = [row["label"] for row in examples]
    correct = sum(predicted == expected for predicted, expected in zip(predictions, labels, strict=True))
    return {
        "status": "synthetic_smoke_only",
        "model_family": "deterministic_keyword_smoke",
        "example_count": len(examples),
        "accuracy": correct / len(examples) if examples else 0.0,
        "label_support": dict(Counter(labels)),
        "output_policy": "no_model_weights_committed",
        "limitations": [
            "synthetic fixture only",
            "not production ML",
            "not a training-quality claim",
        ],
    }


def output_path_is_tmp(path: Path) -> bool:
    try:
        return path.resolve().is_relative_to(Path("/tmp").resolve())
    except AttributeError:  # pragma: no cover - Python <3.9 fallback
        return str(path.resolve()).startswith(str(Path("/tmp").resolve()))
