from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from signal_engine.retrieval.evaluate import load_eval_queries, placeholder_expected_ids, validate_eval_query_record
from signal_engine.retrieval.object_metadata import validate_retrieval_object_metadata_rows
from signal_engine.retrieval.providers.config import ALLOWED_PROVIDER_SLOTS, REAL_PROVIDER_SLOTS, load_provider_config
from signal_engine.retrieval.providers.safety import (
    RESTRICTED_OUTPUT_COMPONENTS,
    validate_provider_output_payload,
    validate_safe_provider_output_path,
)
from signal_engine.retrieval.reviewed_query_set import (
    MIN_REVIEWED_ELIGIBLE_QUERIES,
    REVIEWED_QUERY_SET_STATUS_SMOKE_ONLY_BLOCKED,
    REVIEWED_QUERY_SET_STATUSES,
    is_reviewed_query_set_rows,
    summarize_reviewed_query_set,
    validate_reviewed_query_set_rows,
)

BAKEOFF_STATUS_LABEL = "retrieval_bakeoff_plan_only"
SUPPORTED_BAKEOFF_METRICS = {
    "recall@1",
    "recall@3",
    "recall@5",
    "mrr",
    "exact_evidence_id_hit_rate",
    "citation_validity_rate",
    "invalid_citation_rate",
    "wrong_case_rate",
    "wrong_ticker_rate",
    "wrong_period_rate",
    "abstention_correctness",
    "fallback_overuse_rate",
    "latency_p50",
    "latency_p90",
    "latency_p95",
    "latency_max",
    "provenance_completeness_rate",
}
REQUIRED_MANIFEST_FIELDS = {
    "version",
    "bakeoff_id",
    "status_label",
    "retrieval_objects_path",
    "reviewed_query_set",
    "provider_config_path",
    "provider_slots",
    "metrics_planned",
    "output_root",
    "plan_outputs",
    "network_allowed",
    "local_only_artifact_rules",
    "no_commit_artifact_patterns",
    "claim_flags",
    "reviewer_approval",
}
FORBIDDEN_MANIFEST_CLAIM_PATTERNS = [
    re.compile(r"\bevaluated\s+rag\b", re.IGNORECASE),
    re.compile(r"\bproduction\s+rag\b", re.IGNORECASE),
    re.compile(r"\bproduction\s+retrieval\s+quality\b", re.IGNORECASE),
    re.compile(r"\bbest\s+provider\b", re.IGNORECASE),
    re.compile(r"\bimproved\s+recall\b|\bimproved\s+mrr\b", re.IGNORECASE),
    re.compile(r"\bbuy\b|\bsell\b|\bshort\b|\btrade\b|\btrading\b|\balpha\b", re.IGNORECASE),
    re.compile(r"statistical\s+significance|\bsignificance\s+claim", re.IGNORECASE),
]
FORBIDDEN_QUERY_GATE_KEYS = {
    "answer",
    "answer_text",
    "expected_answer",
    "gold_label",
    "gold_labels",
    "adjudication",
    "adjudication_row",
    "promotion_row",
    "training_label",
}
FORBIDDEN_OUTPUT_ROOT_COMPONENTS = RESTRICTED_OUTPUT_COMPONENTS | {
    "data",
    "reports",
    "docs",
    "configs",
    "schemas",
    "src",
    "tests",
    "tools",
    "provider_outputs",
}
FORBIDDEN_OUTPUT_ROOT_RE = re.compile(r"(embedding|embeddings|vector|vectors|index|indexes|indices|faiss|chroma|lancedb)", re.IGNORECASE)


@dataclass(frozen=True)
class BakeoffManifest:
    path: Path
    payload: dict[str, Any]

    @property
    def query_path(self) -> Path:
        return Path(str(self.payload["reviewed_query_set"]["path"]))

    @property
    def smoke_only(self) -> bool:
        return bool(self.payload["reviewed_query_set"]["smoke_only"])

    @property
    def reviewed(self) -> bool:
        return bool(self.payload["reviewed_query_set"]["reviewed"])

    @property
    def review_stage(self) -> str:
        return str(self.payload["reviewed_query_set"].get("review_stage", "reviewed" if self.reviewed else "smoke_only"))


def repo_path(path: Path, *, root: Path) -> Path:
    return path if path.is_absolute() else root / path


def display_path(path: Path, *, root: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(root))
    except ValueError:
        return str(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{line_number}: expected JSON object")
            rows.append(payload)
    return rows


def read_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("bakeoff manifest must be a mapping")
    return payload


def _walk_strings(payload: Any) -> list[str]:
    values: list[str] = []
    if isinstance(payload, dict):
        for value in payload.values():
            values.extend(_walk_strings(value))
    elif isinstance(payload, list):
        for value in payload:
            values.extend(_walk_strings(value))
    elif isinstance(payload, str):
        values.append(payload)
    return values


def _manifest_claim_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for value in _walk_strings(payload):
        for pattern in FORBIDDEN_MANIFEST_CLAIM_PATTERNS:
            if pattern.search(value):
                errors.append(f"manifest contains overclaiming or unsafe wording: {value!r}")
                break
    claim_flags = payload.get("claim_flags")
    if isinstance(claim_flags, dict):
        for key, value in claim_flags.items():
            if value is not False:
                errors.append(f"claim_flags.{key} must be false")
    return errors


def validate_bakeoff_output_root(path: Path, *, root: Path | None = None) -> list[str]:
    errors: list[str] = []
    parts = [part.lower() for part in path.parts]
    if path.is_absolute():
        if root is not None:
            try:
                path.resolve().relative_to(root.resolve())
                inside_repo = True
            except ValueError:
                inside_repo = False
            if inside_repo:
                errors.append("absolute output_root must not point inside the repository")
    elif not parts or parts[0] != ".local":
        errors.append("relative output_root must be a local-only .local path")
    blocked = sorted(set(parts) & FORBIDDEN_OUTPUT_ROOT_COMPONENTS)
    if blocked:
        errors.append(f"output_root uses restricted component(s): {', '.join(blocked)}")
    if any(FORBIDDEN_OUTPUT_ROOT_RE.search(part) for part in parts):
        errors.append("output_root must not imply embeddings, vectors, indexes, FAISS, Chroma, or LanceDB artifacts")
    return errors


def _validate_nested_mapping(payload: dict[str, Any], field: str, required: set[str], errors: list[str]) -> dict[str, Any]:
    value = payload.get(field)
    if not isinstance(value, dict):
        errors.append(f"{field} must be a mapping")
        return {}
    for missing in sorted(required - set(value)):
        errors.append(f"{field} missing required field {missing}")
    for extra in sorted(set(value) - required):
        errors.append(f"{field} unexpected field {extra}")
    return value


def validate_bakeoff_manifest_payload(payload: dict[str, Any], *, root: Path, require_files: bool = True) -> list[str]:
    errors = validate_provider_output_payload(payload, context="bakeoff manifest")
    for missing in sorted(REQUIRED_MANIFEST_FIELDS - set(payload)):
        errors.append(f"missing required manifest field {missing}")
    for extra in sorted(set(payload) - REQUIRED_MANIFEST_FIELDS):
        errors.append(f"unexpected manifest field {extra}")
    if errors:
        return errors

    if payload.get("version") != 1:
        errors.append("version must be 1")
    if payload.get("status_label") != BAKEOFF_STATUS_LABEL:
        errors.append(f"status_label must be {BAKEOFF_STATUS_LABEL}")
    if not isinstance(payload.get("bakeoff_id"), str) or not payload["bakeoff_id"].strip():
        errors.append("bakeoff_id must be a non-empty string")
    if payload.get("network_allowed") is not False:
        errors.append("network_allowed must be false in committed bakeoff plans")

    slots = payload.get("provider_slots")
    if not isinstance(slots, list) or not slots or any(not isinstance(slot, str) for slot in slots):
        errors.append("provider_slots must be a non-empty array of strings")
        slots = []
    for slot in slots:
        if slot not in ALLOWED_PROVIDER_SLOTS:
            errors.append(f"unknown provider slot {slot}")
        if slot in REAL_PROVIDER_SLOTS and payload.get("network_allowed") is False:
            errors.append(f"real provider slot {slot} cannot be evaluated when network_allowed=false")

    metrics = payload.get("metrics_planned")
    if not isinstance(metrics, list) or not metrics or any(not isinstance(metric, str) for metric in metrics):
        errors.append("metrics_planned must be a non-empty array of strings")
        metrics = []
    for metric in metrics:
        if metric not in SUPPORTED_BAKEOFF_METRICS:
            errors.append(f"unsupported metric {metric}")

    reviewed_query_set = _validate_nested_mapping(
        payload,
        "reviewed_query_set",
        {"path", "reviewed", "smoke_only", "review_stage", "reviewer", "approval_id", "notes"},
        errors,
    )
    if reviewed_query_set:
        if not str(reviewed_query_set.get("path", "")).strip():
            errors.append("reviewed_query_set.path must be present")
        review_stage = reviewed_query_set.get("review_stage")
        if review_stage not in REVIEWED_QUERY_SET_STATUSES:
            errors.append(f"reviewed_query_set.review_stage must be one of {sorted(REVIEWED_QUERY_SET_STATUSES)}")
        if reviewed_query_set.get("reviewed") is not True and reviewed_query_set.get("smoke_only") is not True and review_stage != "review_pending":
            errors.append("unreviewed query sets must be explicitly marked smoke_only=true or review_stage=review_pending")
        if reviewed_query_set.get("reviewed") is True and reviewed_query_set.get("smoke_only") is True:
            errors.append("reviewed query sets cannot also be smoke_only")
        if review_stage == "template_only" and reviewed_query_set.get("smoke_only") is not True:
            errors.append("template_only query sets must be marked smoke_only=true")
        if review_stage == "reviewed" and reviewed_query_set.get("reviewed") is not True:
            errors.append("review_stage=reviewed requires reviewed=true")
        if require_files and str(reviewed_query_set.get("path", "")).strip() and not repo_path(Path(str(reviewed_query_set["path"])), root=root).exists():
            errors.append(f"reviewed_query_set.path does not exist: {reviewed_query_set['path']}")

    output_root = Path(str(payload.get("output_root", "")))
    errors.extend(validate_bakeoff_output_root(output_root, root=root))
    plan_outputs = _validate_nested_mapping(payload, "plan_outputs", {"json_report", "markdown_report"}, errors)
    if plan_outputs:
        for key, value in plan_outputs.items():
            errors.extend(f"plan_outputs.{key}: {error}" for error in validate_safe_provider_output_path(Path(str(value))))

    local_rules = _validate_nested_mapping(
        payload,
        "local_only_artifact_rules",
        {"generated_artifacts_commit_allowed", "output_root_must_be_gitignored", "cleanup_required_before_commit"},
        errors,
    )
    if local_rules:
        if local_rules.get("generated_artifacts_commit_allowed") is not False:
            errors.append("local_only_artifact_rules.generated_artifacts_commit_allowed must be false")
        if local_rules.get("output_root_must_be_gitignored") is not True:
            errors.append("local_only_artifact_rules.output_root_must_be_gitignored must be true")
        if local_rules.get("cleanup_required_before_commit") is not True:
            errors.append("local_only_artifact_rules.cleanup_required_before_commit must be true")

    patterns = payload.get("no_commit_artifact_patterns")
    if not isinstance(patterns, list) or not patterns or any(not isinstance(pattern, str) for pattern in patterns):
        errors.append("no_commit_artifact_patterns must be a non-empty array of strings")

    reviewer = _validate_nested_mapping(
        payload,
        "reviewer_approval",
        {"required_for_real_run", "approved", "reviewer", "approval_date", "approval_id"},
        errors,
    )
    if reviewer:
        if reviewer.get("required_for_real_run") is not True:
            errors.append("reviewer_approval.required_for_real_run must be true")
        if reviewer.get("approved") is not False:
            errors.append("reviewer_approval.approved must be false in committed scaffold manifests")
    errors.extend(_manifest_claim_errors(payload))
    return errors


def load_bakeoff_manifest(path: Path, *, root: Path, require_files: bool = True) -> BakeoffManifest:
    payload = read_yaml(path)
    errors = validate_bakeoff_manifest_payload(payload, root=root, require_files=require_files)
    if errors:
        raise ValueError("; ".join(errors))
    return BakeoffManifest(path=path, payload=payload)


def validate_bakeoff_query_set(
    path: Path,
    *,
    smoke_only: bool,
    reviewed: bool,
    object_rows: list[dict[str, Any]] | None = None,
    allow_template: bool = False,
) -> tuple[list[dict[str, Any]], list[str]]:
    queries = load_eval_queries(path)
    errors: list[str] = []
    if not queries:
        errors.append("reviewed query set is empty")
        return queries, errors
    if is_reviewed_query_set_rows(queries):
        errors.extend(
            validate_reviewed_query_set_rows(
                queries,
                object_rows or [],
                allow_template=allow_template,
            )
        )
        if smoke_only and reviewed:
            errors.append("smoke-only query sets cannot be marked reviewed")
        return queries, errors
    for index, row in enumerate(queries, start=1):
        errors.extend(f"query row {index}: {error}" for error in validate_eval_query_record(row))
        key_errors = validate_provider_output_payload(row, context=f"query row {index}")
        errors.extend(key_errors)
        forbidden_keys = sorted(set(row) & FORBIDDEN_QUERY_GATE_KEYS)
        for key in forbidden_keys:
            errors.append(f"query row {index}: forbidden query gate key {key}")
        if row.get("negative_control") is False and row.get("abstention_expected") is False:
            if "retrieval_object_manifest" not in row.get("rights_required", []):
                errors.append(f"query row {index}: positive rows must require retrieval_object_manifest")
    placeholders = placeholder_expected_ids(queries)
    if placeholders and not smoke_only:
        errors.append("reviewed query set contains placeholder expected evidence IDs")
    if smoke_only and reviewed:
        errors.append("smoke-only query sets cannot be marked reviewed")
    return queries, errors


def _digest_rows(rows: list[dict[str, Any]], *, fields: tuple[str, ...]) -> str:
    digest_rows = [{field: row.get(field, "") for field in fields} for row in rows]
    encoded = json.dumps(digest_rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _legacy_query_set_readiness(queries: list[dict[str, Any]], *, smoke_only: bool, reviewed: bool) -> dict[str, Any]:
    placeholders = placeholder_expected_ids(queries)
    if smoke_only:
        readiness_status = REVIEWED_QUERY_SET_STATUS_SMOKE_ONLY_BLOCKED
    elif reviewed and not placeholders:
        readiness_status = "legacy_reviewed_eval_query_set"
    else:
        readiness_status = "review_pending_blocked"
    return {
        "query_set_readiness_status": readiness_status,
        "query_status_counts": {"legacy_eval_query": len(queries)},
        "reviewed_eligible_query_count": 0,
        "minimum_reviewed_eligible_queries": MIN_REVIEWED_ELIGIBLE_QUERIES,
        "benchmark_threshold_met": False,
        "placeholder_count": len(placeholders),
        "unknown_object_ref_count": 0,
        "has_reviewed_eligible_queries": False,
        "benchmark_ready_query_set": False,
        "benchmark_complete": False,
        "evaluated_retrieval_quality": False,
        "production_rag_claim": False,
    }


def _query_digest_fields(queries: list[dict[str, Any]]) -> tuple[str, ...]:
    if is_reviewed_query_set_rows(queries):
        return ("query_id", "case_id", "query_type", "review_status", "benchmark_eligible")
    return ("query_id", "query_intent", "target_case_id", "target_ticker", "target_fiscal_period")


def build_bakeoff_plan_summary(manifest: BakeoffManifest, *, root: Path) -> dict[str, Any]:
    payload = manifest.payload
    objects_path = repo_path(Path(str(payload["retrieval_objects_path"])), root=root)
    object_rows = read_jsonl(objects_path)
    object_errors = validate_retrieval_object_metadata_rows(object_rows)
    if object_errors:
        raise ValueError("; ".join(object_errors))

    provider_config = load_provider_config(repo_path(Path(str(payload["provider_config_path"])), root=root))
    provider_config_slots = set(provider_config.providers)
    missing_slots = [slot for slot in payload["provider_slots"] if slot not in provider_config_slots]
    if missing_slots:
        raise ValueError("; ".join(f"provider slot {slot} missing from provider config" for slot in missing_slots))

    query_path = repo_path(Path(str(payload["reviewed_query_set"]["path"])), root=root)
    queries, query_errors = validate_bakeoff_query_set(
        query_path,
        smoke_only=bool(payload["reviewed_query_set"]["smoke_only"]),
        reviewed=bool(payload["reviewed_query_set"]["reviewed"]),
        object_rows=object_rows,
        allow_template=True,
    )
    if query_errors:
        raise ValueError("; ".join(query_errors))

    smoke_only = bool(payload["reviewed_query_set"]["smoke_only"])
    if is_reviewed_query_set_rows(queries):
        query_readiness = summarize_reviewed_query_set(queries, object_rows=object_rows)
    else:
        query_readiness = _legacy_query_set_readiness(
            queries,
            smoke_only=smoke_only,
            reviewed=bool(payload["reviewed_query_set"]["reviewed"]),
        )
    real_benchmark_allowed = (
        bool(query_readiness["benchmark_ready_query_set"])
        and not smoke_only
        and bool(payload["reviewed_query_set"]["reviewed"])
        and payload["provider_slots"] != ["local_stub"]
        and payload["network_allowed"] is True
        and payload["reviewer_approval"]["approved"] is True
    )
    summary = {
        "status_label": BAKEOFF_STATUS_LABEL,
        "bakeoff_id": payload["bakeoff_id"],
        "manifest_path": display_path(manifest.path, root=root),
        "retrieval_objects_path": display_path(objects_path, root=root),
        "reviewed_query_set_path": display_path(query_path, root=root),
        "provider_config_path": display_path(repo_path(Path(str(payload["provider_config_path"])), root=root), root=root),
        "provider_slots": payload["provider_slots"],
        "metrics_planned": payload["metrics_planned"],
        "output_root": payload["output_root"],
        "object_count": len(object_rows),
        "query_count": len(queries),
        "smoke_only": smoke_only,
        "reviewed_query_set": bool(payload["reviewed_query_set"]["reviewed"]),
        "query_set_review_stage": str(payload["reviewed_query_set"].get("review_stage", "")),
        "query_set_readiness_status": query_readiness["query_set_readiness_status"],
        "query_status_counts": query_readiness["query_status_counts"],
        "reviewed_eligible_query_count": query_readiness["reviewed_eligible_query_count"],
        "minimum_reviewed_eligible_queries": query_readiness["minimum_reviewed_eligible_queries"],
        "benchmark_threshold_met": query_readiness["benchmark_threshold_met"],
        "placeholder_count": query_readiness["placeholder_count"],
        "unknown_object_ref_count": query_readiness["unknown_object_ref_count"],
        "has_reviewed_eligible_queries": query_readiness["has_reviewed_eligible_queries"],
        "benchmark_ready_query_set": query_readiness["benchmark_ready_query_set"],
        "real_benchmark_allowed": real_benchmark_allowed,
        "network_calls": False,
        "embeddings_generated": False,
        "vector_db_generated": False,
        "benchmark_complete": False,
        "evaluated_retrieval_quality": False,
        "provider_benchmark_complete": False,
        "production_rag_claim": False,
        "object_metadata_digest": _digest_rows(object_rows, fields=("object_id", "object_type", "case_id", "text_hash", "provenance_hash")),
        "query_set_digest": _digest_rows(queries, fields=_query_digest_fields(queries)),
        "blockers_before_real_benchmark": [
            "benchmark-ready reviewed query-set inputs required" if not query_readiness["benchmark_ready_query_set"] else "",
            f"at least {MIN_REVIEWED_ELIGIBLE_QUERIES} reviewed benchmark-eligible query rows required"
            if int(query_readiness["reviewed_eligible_query_count"]) < MIN_REVIEWED_ELIGIBLE_QUERIES
            else "",
            "placeholder query references must be removed" if query_readiness["placeholder_count"] else "",
            "unknown object references must be resolved" if query_readiness["unknown_object_ref_count"] else "",
            "reviewer approval required" if payload["reviewer_approval"]["approved"] is not True else "",
            "real provider config must remain non-committed until approved" if payload["provider_slots"] == ["local_stub"] else "",
            "network calls remain disabled in committed scaffold" if payload["network_allowed"] is False else "",
        ],
    }
    summary["blockers_before_real_benchmark"] = [item for item in summary["blockers_before_real_benchmark"] if item]
    report_errors = validate_provider_output_payload(summary, context="bakeoff plan summary")
    if report_errors:
        raise ValueError("; ".join(report_errors))
    return summary


def write_plan_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_plan_markdown(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Retrieval Bakeoff Plan",
        "",
        "## Run status",
        f"- status: `{payload['status_label']}`",
        f"- network calls: `{str(payload['network_calls']).lower()}`",
        f"- embeddings generated: `{str(payload['embeddings_generated']).lower()}`",
        f"- vector DB generated: `{str(payload['vector_db_generated']).lower()}`",
        f"- benchmark complete: `{str(payload['benchmark_complete']).lower()}`",
        f"- evaluated retrieval quality: `{str(payload['evaluated_retrieval_quality']).lower()}`",
        f"- production RAG claim: `{str(payload['production_rag_claim']).lower()}`",
        "",
        "## Inputs",
        f"- manifest: `{payload['manifest_path']}`",
        f"- retrieval objects: `{payload['retrieval_objects_path']}`",
        f"- query set: `{payload['reviewed_query_set_path']}`",
        f"- provider config: `{payload['provider_config_path']}`",
        f"- output root: `{payload['output_root']}`",
        "",
        "## Query gate",
        f"- query count: `{payload['query_count']}`",
        f"- smoke_only: `{str(payload['smoke_only']).lower()}`",
        f"- reviewed_query_set: `{str(payload['reviewed_query_set']).lower()}`",
        f"- query_set_review_stage: `{payload['query_set_review_stage']}`",
        f"- query_set_readiness_status: `{payload['query_set_readiness_status']}`",
        f"- reviewed eligible query rows: `{payload['reviewed_eligible_query_count']}`",
        f"- minimum reviewed eligible query rows: `{payload['minimum_reviewed_eligible_queries']}`",
        f"- benchmark_threshold_met: `{str(payload['benchmark_threshold_met']).lower()}`",
        f"- benchmark-ready inputs only: `{str(payload['benchmark_ready_query_set']).lower()}`",
        f"- real_benchmark_allowed: `{str(payload['real_benchmark_allowed']).lower()}`",
        f"- placeholder references: `{payload['placeholder_count']}`",
        f"- unknown object references: `{payload['unknown_object_ref_count']}`",
        "",
        "## Query status counts",
    ]
    lines.extend(f"- {status}: `{count}`" for status, count in payload["query_status_counts"].items())
    lines.extend(
        [
            "",
            "## Provider slots",
        ]
    )
    lines.extend(f"- `{slot}`" for slot in payload["provider_slots"])
    lines.extend(["", "## Planned metrics"])
    lines.extend(f"- `{metric}`" for metric in payload["metrics_planned"])
    lines.extend(
        [
            "",
            "## Metadata digests",
            f"- retrieval objects: `{payload['object_metadata_digest']}`",
            f"- query set: `{payload['query_set_digest']}`",
            "",
            "## Blockers before real benchmark",
        ]
    )
    lines.extend(f"- {item}" for item in payload["blockers_before_real_benchmark"])
    lines.extend(
        [
            "",
            "## Safety",
            "- This plan emits safe plan metadata only.",
            "- It does not generate embeddings, vector stores, provider response payloads, raw text, benchmark scores, labels, adjudication rows, training data, or promotion rows.",
            "- Current status remains scaffold-only until reviewed query sets, provider approval, artifact gates, provenance gates, and citation gates are complete.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
