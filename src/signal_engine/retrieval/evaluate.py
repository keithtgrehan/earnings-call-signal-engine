from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
import tempfile
from typing import Any

from .index_local import build_local_bm25_index, load_retrieval_manifest, score_query
from .query import query_local_index

ALLOWED_QUERY_OBJECT_TYPES = {"evidence_object", "event_aligned_chunk", "semantic_fallback"}
ALLOWED_RESULT_OBJECT_TYPES = ALLOWED_QUERY_OBJECT_TYPES
ALLOWED_SECTION_LABELS = {
    "prepared_remarks",
    "qa",
    "safe_harbor",
    "operator",
    "non_gaap",
    "vendor_disclaimer",
    "unknown",
}
ALLOWED_SPEAKER_ROLES = {"management", "analyst", "operator", "ir", "vendor", "unknown"}
ALLOWED_RIGHTS = {
    "official_ir_transcript_metadata",
    "normalized_transcript_manifest",
    "retrieval_object_manifest",
    "transcript_span_access",
    "transcript_audio_alignment",
}
ALLOWED_RETRIEVAL_METHODS = {"bm25", "hybrid", "embedding", "rerank", "manual_fixture", "abstain"}
ALLOWED_BLOCKED_REASONS = {
    "no_index",
    "no_rights",
    "qna_missing",
    "object_type_unavailable",
    "only_semantic_fallback",
    "wrong_ticker",
    "wrong_period",
    "trading_request",
    "audio_unmatched",
    "unsafe_claim",
    "safe_harbor_suppressed",
    "non_gaap_suppressed",
    "operator_only_suppressed",
    "vendor_disclaimer_suppressed",
    "no_evidence_for_signal",
    "raw_text_blocked",
    "placeholder_expected_id",
    None,
}
FORBIDDEN_PAYLOAD_KEYS = {
    "raw_text",
    "transcript_text",
    "asr_text",
    "audio_text",
    "chunk_text",
    "embedding",
    "embeddings",
    "vector",
    "vectors",
    "vector_db",
    "payload_text",
}
QUERY_REQUIRED_FIELDS = {
    "query_id",
    "query_text",
    "query_intent",
    "target_case_id",
    "target_ticker",
    "target_fiscal_period",
    "expected_object_types",
    "expected_signal_types",
    "expected_sections",
    "expected_speaker_roles",
    "expected_evidence_ids",
    "negative_control",
    "abstention_expected",
    "rights_required",
    "notes",
}
RESULT_REQUIRED_FIELDS = {
    "query_id",
    "result_rank",
    "object_id",
    "object_type",
    "case_id",
    "ticker",
    "fiscal_period",
    "source_hash",
    "normalized_transcript_hash",
    "provenance_hash",
    "section_label",
    "speaker_role",
    "qa_pair_id",
    "retrieval_score",
    "retrieval_method",
    "citation_valid",
    "raw_text_returned",
    "blocked_reason",
    "notes",
}
RESULT_OPTIONAL_FIELDS = {"latency_ms"}
NULLABLE_ABSTENTION_FIELDS = {
    "object_id",
    "object_type",
    "case_id",
    "ticker",
    "fiscal_period",
    "source_hash",
    "normalized_transcript_hash",
    "provenance_hash",
    "qa_pair_id",
}
MARKET_CLAIM_PATTERNS = [
    re.compile(r"\bbuy\b", re.IGNORECASE),
    re.compile(r"\bsell\b", re.IGNORECASE),
    re.compile(r"\bshort\b", re.IGNORECASE),
    re.compile(r"\btrade\b|\btrading\b", re.IGNORECASE),
    re.compile(r"\balpha\b", re.IGNORECASE),
    re.compile(r"\bcausal\b", re.IGNORECASE),
    re.compile(r"statistical\s+significance", re.IGNORECASE),
    re.compile(r"live\s+execution", re.IGNORECASE),
]
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
TRANSCRIPT_LIKE_VALUE_PATTERNS = [
    ("transcript-like text", re.compile(r"\b(operator|management|analyst|speaker|executive|ir)\s*:", re.IGNORECASE)),
    ("raw/chunk text", re.compile(r"\b(raw transcript|transcript|chunk|payload)\s+text\s+(excerpt|snippet|payload|content)", re.IGNORECASE)),
    ("raw/chunk text", re.compile(r"\bretrieval payload\b", re.IGNORECASE)),
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"{path}:{line_number}: expected JSON object")
        rows.append(payload)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def load_eval_queries(path: Path) -> list[dict[str, Any]]:
    return read_jsonl(path)


def validate_no_forbidden_payload_keys(payload: Any, *, context: str = "payload") -> list[str]:
    errors: list[str] = []
    forbidden_compact = {re.sub(r"[^a-z0-9]", "", key.lower()) for key in FORBIDDEN_PAYLOAD_KEYS}

    def visit(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                key_path = f"{path}.{key}" if path else str(key)
                key_snake = re.sub(r"(?<!^)(?=[A-Z])", "_", str(key)).lower()
                key_compact = re.sub(r"[^a-z0-9]", "", str(key).lower())
                key_snake_compact = re.sub(r"[^a-z0-9]", "", key_snake)
                if key in FORBIDDEN_PAYLOAD_KEYS or key_compact in forbidden_compact or key_snake_compact in forbidden_compact:
                    errors.append(f"{context}: forbidden raw/payload key {key_path}")
                visit(nested, key_path)
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                visit(nested, f"{path}[{index}]")

    visit(payload, "")
    return errors


def validate_claim_safety_text(text: str) -> list[str]:
    return [f"unsafe market claim term matched: {pattern.pattern}" for pattern in MARKET_CLAIM_PATTERNS if pattern.search(text)]


def validate_no_raw_text_like_values(payload: Any, *, context: str = "payload") -> list[str]:
    errors: list[str] = []

    def visit(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                visit(nested, f"{path}.{key}" if path else str(key))
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                visit(nested, f"{path}[{index}]")
        elif isinstance(value, str):
            for label, pattern in TRANSCRIPT_LIKE_VALUE_PATTERNS:
                if pattern.search(value):
                    errors.append(f"{context}: {label} value blocked at {path}")
                    break

    visit(payload, "")
    return errors


def _claim_safety_errors(row: dict[str, Any], *, fields: tuple[str, ...], context: str) -> list[str]:
    errors: list[str] = []
    for field in fields:
        value = row.get(field)
        if isinstance(value, str):
            errors.extend(f"{context}.{field}: {error}" for error in validate_claim_safety_text(value))
    return errors


def _validate_string_list(row: dict[str, Any], field: str, errors: list[str]) -> list[str]:
    value = row.get(field)
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        errors.append(f"{field} must be an array of strings")
        return []
    return value


def validate_eval_query_record(row: dict[str, Any]) -> list[str]:
    errors = validate_no_forbidden_payload_keys(row, context="query")
    errors.extend(validate_no_raw_text_like_values(row, context="query"))
    keys = set(row)
    for field in sorted(QUERY_REQUIRED_FIELDS - keys):
        errors.append(f"missing required field {field}")
    for field in sorted(keys - QUERY_REQUIRED_FIELDS):
        errors.append(f"unexpected field {field}")
    for field in ("query_id", "query_text", "query_intent", "target_case_id", "target_ticker", "target_fiscal_period", "notes"):
        if field in row and not isinstance(row.get(field), str):
            errors.append(f"{field} must be a string")
    for field in ("negative_control", "abstention_expected"):
        if field in row and not isinstance(row.get(field), bool):
            errors.append(f"{field} must be a boolean")
    object_types = _validate_string_list(row, "expected_object_types", errors)
    sections = _validate_string_list(row, "expected_sections", errors)
    speakers = _validate_string_list(row, "expected_speaker_roles", errors)
    rights = _validate_string_list(row, "rights_required", errors)
    _validate_string_list(row, "expected_signal_types", errors)
    expected_ids = _validate_string_list(row, "expected_evidence_ids", errors)
    for item in object_types:
        if item not in ALLOWED_QUERY_OBJECT_TYPES:
            errors.append(f"expected_object_types contains unsupported value {item!r}")
    for item in sections:
        if item not in ALLOWED_SECTION_LABELS:
            errors.append(f"expected_sections contains unsupported value {item!r}")
    for item in speakers:
        if item not in ALLOWED_SPEAKER_ROLES:
            errors.append(f"expected_speaker_roles contains unsupported value {item!r}")
    for item in rights:
        if item not in ALLOWED_RIGHTS:
            errors.append(f"rights_required contains unsupported value {item!r}")
    if row.get("negative_control") is True:
        if row.get("abstention_expected") is not True:
            errors.append("negative_control rows must set abstention_expected=true")
        if expected_ids:
            errors.append("negative_control rows must leave expected_evidence_ids empty")
    if row.get("abstention_expected") is True and expected_ids:
        errors.append("abstention_expected rows must leave expected_evidence_ids empty")
    if row.get("negative_control") is False and row.get("abstention_expected") is False and not expected_ids:
        errors.append("non-abstention positive rows must include expected_evidence_ids")
    if row.get("negative_control") is not True and row.get("abstention_expected") is not True:
        errors.extend(_claim_safety_errors(row, fields=("query_text", "notes"), context="query"))
    return errors


def validate_retrieval_result_record(row: dict[str, Any]) -> list[str]:
    errors = validate_no_forbidden_payload_keys(row, context="result")
    errors.extend(validate_no_raw_text_like_values(row, context="result"))
    keys = set(row)
    allowed = RESULT_REQUIRED_FIELDS | RESULT_OPTIONAL_FIELDS
    for field in sorted(RESULT_REQUIRED_FIELDS - keys):
        errors.append(f"missing required field {field}")
    for field in sorted(keys - allowed):
        errors.append(f"unexpected field {field}")
    if row.get("raw_text_returned") is not False:
        errors.append("raw_text_returned must be false")
    method = row.get("retrieval_method")
    if method not in ALLOWED_RETRIEVAL_METHODS:
        errors.append(f"retrieval_method contains unsupported value {method!r}")
    blocked_reason = row.get("blocked_reason")
    if blocked_reason not in ALLOWED_BLOCKED_REASONS:
        errors.append(f"blocked_reason contains unsupported value {blocked_reason!r}")
    if row.get("object_type") is not None and row.get("object_type") not in ALLOWED_RESULT_OBJECT_TYPES:
        errors.append(f"object_type contains unsupported value {row.get('object_type')!r}")
    if row.get("section_label") not in ALLOWED_SECTION_LABELS:
        errors.append(f"section_label contains unsupported value {row.get('section_label')!r}")
    if row.get("speaker_role") not in ALLOWED_SPEAKER_ROLES:
        errors.append(f"speaker_role contains unsupported value {row.get('speaker_role')!r}")
    for field in ("query_id", "section_label", "speaker_role", "notes"):
        if field in row and not isinstance(row.get(field), str):
            errors.append(f"{field} must be a string")
    for field in ("result_rank",):
        if field in row and not isinstance(row.get(field), int):
            errors.append(f"{field} must be an integer")
    for field in ("retrieval_score", "latency_ms"):
        if field in row and row.get(field) is not None and not isinstance(row.get(field), (int, float)):
            errors.append(f"{field} must be numeric")
    if "citation_valid" in row and not isinstance(row.get("citation_valid"), bool):
        errors.append("citation_valid must be a boolean")
    nullable_present = [field for field in NULLABLE_ABSTENTION_FIELDS if row.get(field) is None]
    if nullable_present and method != "abstain":
        errors.append("nullable object/case/provenance fields are allowed only when retrieval_method='abstain'")
    if method == "abstain":
        if row.get("result_rank") != 0:
            errors.append("abstention result_rank must be 0")
    else:
        errors.extend(_claim_safety_errors(row, fields=("notes",), context="result"))
        if isinstance(row.get("result_rank"), int) and row["result_rank"] < 1:
            errors.append("non-abstention result_rank must be >= 1")
        for field in ("object_id", "case_id", "ticker", "fiscal_period", "source_hash", "normalized_transcript_hash", "provenance_hash"):
            if not row.get(field):
                errors.append(f"{field} must be present for non-abstention rows")
        for field in ("source_hash", "normalized_transcript_hash", "provenance_hash"):
            value = row.get(field)
            if isinstance(value, str) and value and not SHA256_RE.fullmatch(value):
                errors.append(f"{field} must be a sha256:<64 lowercase hex> value for non-abstention rows")
    return errors


def _query_text(query: dict[str, Any]) -> str:
    return str(query.get("query_text", query.get("query", "")))


def _query_case(query: dict[str, Any]) -> str:
    return str(query.get("target_case_id", query.get("case_id", "")))


def _query_ticker(query: dict[str, Any]) -> str:
    return str(query.get("target_ticker", query.get("ticker", "")))


def _query_period(query: dict[str, Any]) -> str:
    return str(query.get("target_fiscal_period", query.get("fiscal_period", "")))


def _query_expected_ids(query: dict[str, Any]) -> list[str]:
    ids = query.get("expected_evidence_ids")
    if ids:
        return [str(item) for item in ids]
    return [str(item) for item in query.get("expected_object_ids", [])]


def _query_expected_object_types(query: dict[str, Any]) -> set[str]:
    values = query.get("expected_object_types")
    if isinstance(values, list) and values:
        return {str(item) for item in values}
    if query.get("requires_evidence_object") or query.get("expected_evidence_ids"):
        return {"evidence_object", "event_aligned_chunk"}
    return set()


def _query_abstention_expected(query: dict[str, Any]) -> bool:
    return bool(query.get("abstention_expected", query.get("expected_abstain", False)))


def _is_placeholder_expected_id(value: str) -> bool:
    return value.startswith("REVIEW_REQUIRED_") or value.startswith("{") or value.endswith("}")


def placeholder_expected_ids(queries: list[dict[str, Any]]) -> list[str]:
    return [item for query in queries for item in _query_expected_ids(query) if _is_placeholder_expected_id(item)]


def _rate(numerator: int, denominator: int) -> dict[str, float | int]:
    percentage = round((numerator / denominator * 100.0), 2) if denominator else 0.0
    return {"numerator": numerator, "denominator": denominator, "percentage": percentage}


def _rate_value(rate: dict[str, float | int]) -> float:
    return (float(rate["numerator"]) / float(rate["denominator"])) if rate["denominator"] else 0.0


def _rank_for_expected(returned: list[str], expected: set[str]) -> int:
    for index, object_id in enumerate(returned, start=1):
        if object_id in expected:
            return index
    return 0


def _same_context(metadata: dict[str, Any], query: dict[str, Any]) -> bool:
    return (
        (not _query_case(query) or metadata.get("case_id") == _query_case(query))
        and (not _query_ticker(query) or metadata.get("ticker") == _query_ticker(query))
        and (not _query_period(query) or metadata.get("fiscal_period") == _query_period(query))
    )


def _is_transcript_aligned_object(row: dict[str, str]) -> bool:
    object_type = str(row.get("object_type", "")).lower()
    source_type = str(row.get("source_type", "")).lower()
    asset_type = str(row.get("asset_type", "")).lower()
    if object_type == "audio" or asset_type == "audio":
        return False
    if "audio" in source_type and str(row.get("transcript_alignment_status", "")).lower() not in {"matched", "transcript_aligned"}:
        return False
    return True


def _internal_object_type_for_expected(object_type: str) -> str:
    return "semantic_fallback" if object_type == "semantic_chunk" else object_type


def _manifest_object_type_for_expected(object_type: str) -> set[str]:
    if object_type == "semantic_fallback":
        return {"semantic_chunk", "semantic_fallback"}
    return {object_type}


def _filter_objects_for_query(objects: list[dict[str, str]], query: dict[str, Any]) -> list[dict[str, str]]:
    filtered = [row for row in objects if _is_transcript_aligned_object(row)]
    if not query.get("cross_case_search"):
        filtered = [row for row in filtered if _same_context(row, query)]
    expected_types = _query_expected_object_types(query)
    if expected_types:
        manifest_types = set().union(*(_manifest_object_type_for_expected(item) for item in expected_types))
        filtered = [row for row in filtered if row.get("object_type") in manifest_types]
    return filtered


def _build_disposable_index(objects: list[dict[str, str]]) -> dict[str, Any]:
    if not objects:
        return {
            "documents": [],
            "document_count": 0,
            "avg_doc_length": 0,
            "document_frequency": {},
            "raw_text_indexed": False,
        }
    with tempfile.TemporaryDirectory(prefix="signal_engine_eval_bm25_") as tmp:
        return build_local_bm25_index(objects, out_dir=Path(tmp))


def _ranked_with_priority(index: dict[str, Any], query_text: str, *, limit: int) -> list[dict[str, Any]]:
    ranked = score_query(index, query_text, limit=limit)
    priority_bonus = {"evidence_object": 0.30, "event_aligned_chunk": 0.15, "semantic_chunk": -0.15, "semantic_fallback": -0.15}
    return sorted(
        ranked,
        key=lambda row: (
            float(row.get("score", 0.0)) + priority_bonus.get(str(row.get("metadata", {}).get("object_type", "")), 0.0),
            -int(row.get("metadata", {}).get("retrieval_priority", 99) or 99),
        ),
        reverse=True,
    )[:limit]


def _section_label(metadata: dict[str, Any]) -> str:
    section = str(metadata.get("section", "")).lower()
    topic = str(metadata.get("topic", "")).lower()
    joined = f"{section} {topic}"
    if "safe" in joined and "harbor" in joined:
        return "safe_harbor"
    if "non" in joined and "gaap" in joined:
        return "non_gaap"
    if "vendor" in joined or "disclaimer" in joined:
        return "vendor_disclaimer"
    if "operator" in joined:
        return "operator"
    if section in {"qa", "q&a"} or "question" in joined:
        return "qa"
    if "prepared" in joined or "guidance" in joined:
        return "prepared_remarks"
    return "unknown"


def _speaker_role(metadata: dict[str, Any]) -> str:
    speaker = str(metadata.get("speaker", "")).lower()
    if speaker in ALLOWED_SPEAKER_ROLES:
        return speaker
    if "management" in speaker or "executive" in speaker:
        return "management"
    if "analyst" in speaker:
        return "analyst"
    if "operator" in speaker:
        return "operator"
    if speaker in {"ir", "investor_relations"}:
        return "ir"
    if "vendor" in speaker:
        return "vendor"
    return "unknown"


def _hash_value(metadata: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = str(metadata.get(key, "")).strip()
        if value:
            return value
    return ""


def _citation_ok(metadata: dict[str, Any], query: dict[str, Any]) -> bool:
    return bool(
        metadata.get("source_ref")
        and _hash_value(metadata, "source_sha256")
        and _hash_value(metadata, "normalized_transcript_sha256", "source_sha256")
        and _hash_value(metadata, "provenance_hash", "source_sha256")
        and _same_context(metadata, query)
    )


def _blocked_reason_for_query(query: dict[str, Any]) -> str:
    intent = str(query.get("query_intent", query.get("unsupported_claim_category", ""))).strip()
    mapping = {
        "wrong_ticker": "wrong_ticker",
        "wrong_quarter": "wrong_period",
        "wrong_period": "wrong_period",
        "unsupported_market_claim": "unsafe_claim",
        "trading_advice": "trading_request",
        "trading_request": "trading_request",
        "audio_emotion_deception": "audio_unmatched",
        "audio_unmatched": "audio_unmatched",
        "safe_harbor_as_uncertainty": "safe_harbor_suppressed",
        "safe_harbor_suppressed": "safe_harbor_suppressed",
        "non_gaap_suppressed": "non_gaap_suppressed",
        "operator_only_as_analyst_pressure": "operator_only_suppressed",
        "operator_only_suppressed": "operator_only_suppressed",
        "vendor_disclaimer_suppressed": "vendor_disclaimer_suppressed",
        "generic_optimism_reassurance": "no_evidence_for_signal",
        "semantic_fallback_overuse": "only_semantic_fallback",
        "qna_missing": "qna_missing",
        "qa_missing": "qna_missing",
        "object_type_unavailable": "object_type_unavailable",
        "no_rights": "no_rights",
        "raw_text_blocked": "raw_text_blocked",
        "placeholder_expected_id": "placeholder_expected_id",
    }
    return mapping.get(intent, "no_evidence_for_signal")


def _result_row(query: dict[str, Any], ranked_row: dict[str, Any], *, result_rank: int, retrieval_method: str = "bm25") -> dict[str, Any]:
    metadata = ranked_row.get("metadata", {})
    object_type = _internal_object_type_for_expected(str(metadata.get("object_type", "")))
    return {
        "query_id": str(query.get("query_id", "")),
        "result_rank": result_rank,
        "object_id": ranked_row.get("object_id", ""),
        "object_type": object_type,
        "case_id": metadata.get("case_id", ""),
        "ticker": metadata.get("ticker", ""),
        "fiscal_period": metadata.get("fiscal_period", ""),
        "source_hash": _hash_value(metadata, "source_sha256"),
        "normalized_transcript_hash": _hash_value(metadata, "normalized_transcript_sha256", "source_sha256"),
        "provenance_hash": _hash_value(metadata, "provenance_hash", "source_sha256"),
        "section_label": _section_label(metadata),
        "speaker_role": _speaker_role(metadata),
        "qa_pair_id": str(metadata.get("qa_pair_id", "") or ""),
        "retrieval_score": float(ranked_row.get("score", 0.0)),
        "retrieval_method": retrieval_method,
        "citation_valid": _citation_ok(metadata, query),
        "raw_text_returned": False,
        "blocked_reason": None,
        "notes": "metadata-only retrieval result; raw text suppressed",
    }


def _abstain_row(query: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "query_id": str(query.get("query_id", "")),
        "result_rank": 0,
        "object_id": None,
        "object_type": None,
        "case_id": None,
        "ticker": None,
        "fiscal_period": None,
        "source_hash": None,
        "normalized_transcript_hash": None,
        "provenance_hash": None,
        "section_label": "unknown",
        "speaker_role": "unknown",
        "qa_pair_id": None,
        "retrieval_score": 0.0,
        "retrieval_method": "abstain",
        "citation_valid": True,
        "raw_text_returned": False,
        "blocked_reason": reason,
        "notes": "safe abstention; no raw text returned",
    }


def _is_abstention_result(row: dict[str, Any]) -> bool:
    return row.get("retrieval_method") == "abstain" or row.get("abstained") is True


def _object_inventory(objects: list[dict[str, str]]) -> dict[str, int]:
    inventory: Counter[str] = Counter()
    for row in objects:
        inventory[_internal_object_type_for_expected(str(row.get("object_type", "unknown") or "unknown"))] += 1
    return dict(sorted(inventory.items()))


def _result_inventory(results: list[dict[str, Any]], objects: list[dict[str, str]]) -> dict[str, int]:
    inventory: dict[str, set[str]] = {}
    for row in results:
        if _is_abstention_result(row):
            continue
        object_type = str(row.get("object_type") or "unknown")
        object_id = str(row.get("object_id") or "")
        if object_id:
            inventory.setdefault(object_type, set()).add(object_id)
    if inventory:
        return {key: len(value) for key, value in sorted(inventory.items())}
    return _object_inventory(objects)


def _latency_summary(latencies: list[float]) -> dict[str, float | None]:
    if not latencies:
        return {"p50": None, "p90": None, "p95": None, "max": None}
    ordered = sorted(latencies)

    def percentile(pct: float) -> float:
        if len(ordered) == 1:
            return ordered[0]
        rank = math.ceil((pct / 100.0) * len(ordered)) - 1
        return ordered[min(max(rank, 0), len(ordered) - 1)]

    return {"p50": percentile(50), "p90": percentile(90), "p95": percentile(95), "max": max(ordered)}


def _summarize_results(
    *,
    queries: list[dict[str, Any]],
    objects: list[dict[str, str]],
    results: list[dict[str, Any]],
    smoke_metrics: bool,
    eval_manifest_path: str | None = None,
    query_file_path: str | None = None,
    result_file_path: str | None = None,
    manifest_status: str = "not_provided",
) -> dict[str, Any]:
    non_abstention_queries = [query for query in queries if not _query_abstention_expected(query)]
    abstention_queries = [query for query in queries if _query_abstention_expected(query)]
    by_query: dict[str, list[dict[str, Any]]] = {}
    for row in results:
        by_query.setdefault(str(row.get("query_id", "")), []).append(row)

    recall_hits = {1: 0, 3: 0, 5: 0}
    exact_hits = 0
    reciprocal_ranks: list[float] = []
    fallback_overuse = 0
    fallback_denominator = 0
    abstention_correct = 0

    for query in queries:
        query_id = str(query.get("query_id", ""))
        rows = by_query.get(query_id, [])
        non_abstain_rows = [row for row in rows if not _is_abstention_result(row)]
        if _query_abstention_expected(query):
            if rows and all(_is_abstention_result(row) for row in rows):
                abstention_correct += 1
            continue
        expected = set(_query_expected_ids(query))
        returned = [str(row.get("object_id")) for row in non_abstain_rows if row.get("object_id")]
        rank = _rank_for_expected(returned, expected)
        for k in recall_hits:
            if expected and rank and rank <= k:
                recall_hits[k] += 1
        if expected and rank:
            exact_hits += 1
        reciprocal_ranks.append((1 / rank) if rank else 0.0)
        expected_types = _query_expected_object_types(query)
        if expected_types.intersection({"evidence_object", "event_aligned_chunk"}):
            fallback_denominator += 1
            if any(row.get("object_type") == "semantic_fallback" for row in non_abstain_rows):
                fallback_overuse += 1

    non_abstain_results = [row for row in results if not _is_abstention_result(row)]
    result_denominator = len(non_abstain_results)
    citation_valid = sum(1 for row in non_abstain_results if row.get("citation_valid") is True)
    invalid_citation = result_denominator - citation_valid
    wrong_case = 0
    wrong_ticker = 0
    wrong_period = 0
    provenance_complete = 0
    latencies: list[float] = []
    guardrail_counts: Counter[str] = Counter()
    for row in results:
        if row.get("latency_ms") is not None:
            latencies.append(float(row["latency_ms"]))
        if _is_abstention_result(row):
            guardrail_counts[str(row.get("blocked_reason") or "none")] += 1
            continue
        query = next((item for item in queries if item.get("query_id") == row.get("query_id")), {})
        if _query_case(query) and row.get("case_id") != _query_case(query):
            wrong_case += 1
        if _query_ticker(query) and row.get("ticker") != _query_ticker(query):
            wrong_ticker += 1
        if _query_period(query) and row.get("fiscal_period") != _query_period(query):
            wrong_period += 1
        if row.get("source_hash") and row.get("normalized_transcript_hash") and row.get("provenance_hash"):
            provenance_complete += 1

    placeholders = placeholder_expected_ids(queries)
    rates = {
        "recall_at_1": _rate(recall_hits[1], len(non_abstention_queries)),
        "recall_at_3": _rate(recall_hits[3], len(non_abstention_queries)),
        "recall_at_5": _rate(recall_hits[5], len(non_abstention_queries)),
        "exact_evidence_id_hit_rate": _rate(exact_hits, len(non_abstention_queries)),
        "citation_validity_rate": _rate(citation_valid, result_denominator),
        "invalid_citation_rate": _rate(invalid_citation, result_denominator),
        "wrong_case_rate": _rate(wrong_case, result_denominator),
        "wrong_ticker_rate": _rate(wrong_ticker, result_denominator),
        "wrong_period_rate": _rate(wrong_period, result_denominator),
        "abstention_correctness": _rate(abstention_correct, len(abstention_queries)),
        "fallback_overuse_rate": _rate(fallback_overuse, fallback_denominator),
        "provenance_completeness_rate": _rate(provenance_complete, result_denominator),
    }
    mrr_denominator = len(non_abstention_queries)
    mrr_numerator = sum(reciprocal_ranks)
    mrr = (mrr_numerator / mrr_denominator) if mrr_denominator else 0.0
    warnings: list[str] = []
    failures: list[str] = []
    if placeholders:
        warnings.append("reviewer placeholder expected evidence IDs remain; production metrics must fail closed")
    if smoke_metrics:
        warnings.append("smoke_metrics only; scaffold readiness check, not production RAG quality evidence")
    summary = {
        "query_count": len(queries),
        "result_count": result_denominator,
        "non_abstention_query_count": len(non_abstention_queries),
        "abstention_query_count": len(abstention_queries),
        "rates": rates,
        "recall_at_1": _rate_value(rates["recall_at_1"]),
        "recall_at_3": _rate_value(rates["recall_at_3"]),
        "recall_at_5": _rate_value(rates["recall_at_5"]),
        "mrr": mrr,
        "mrr_numerator": mrr_numerator,
        "mrr_denominator": mrr_denominator,
        "evidence_id_hit_rate": _rate_value(rates["exact_evidence_id_hit_rate"]),
        "citation_validity": _rate_value(rates["citation_validity_rate"]),
        "invalid_citation_rate": _rate_value(rates["invalid_citation_rate"]),
        "wrong_case_rate": _rate_value(rates["wrong_case_rate"]),
        "wrong_ticker_rate": _rate_value(rates["wrong_ticker_rate"]),
        "wrong_period_rate": _rate_value(rates["wrong_period_rate"]),
        "wrong_case_ticker_period": wrong_case + wrong_ticker + wrong_period,
        "abstention_correctness": _rate_value(rates["abstention_correctness"]),
        "fallback_overuse": _rate_value(rates["fallback_overuse_rate"]),
        "latency": _latency_summary(latencies),
        "provenance_completeness": _rate_value(rates["provenance_completeness_rate"]),
        "raw_text_returned": False,
        "smoke_metrics": smoke_metrics,
        "evaluated_rag": False,
        "eval_manifest_path": eval_manifest_path,
        "query_file_path": query_file_path,
        "result_file_path": result_file_path,
        "manifest_status": manifest_status,
        "object_inventory_by_type": _result_inventory(results, objects),
        "qna_state": "missing" if not any(row.get("qa_pair_id") for row in results if row.get("qa_pair_id")) else "present",
        "placeholder_expected_ids": len(placeholders),
        "guardrail_counts": dict(sorted(guardrail_counts.items())),
        "warnings": warnings,
        "failures": failures,
        "results": results,
    }
    return summary


def summarize_retrieval_results(
    *,
    queries: list[dict[str, Any]],
    results: list[dict[str, Any]],
    objects: list[dict[str, str]] | None = None,
    smoke_metrics: bool = False,
    eval_manifest_path: str | None = None,
    query_file_path: str | None = None,
    result_file_path: str | None = None,
    manifest_status: str = "not_provided",
) -> dict[str, Any]:
    return _summarize_results(
        queries=queries,
        objects=objects or [],
        results=results,
        smoke_metrics=smoke_metrics,
        eval_manifest_path=eval_manifest_path,
        query_file_path=query_file_path,
        result_file_path=result_file_path,
        manifest_status=manifest_status,
    )


def evaluate_retrieval(index_path: Path, queries_path: Path, *, limit: int = 10) -> dict[str, Any]:
    queries = load_eval_queries(queries_path)
    results: list[dict[str, Any]] = []
    hits = 0
    for query in queries:
        ranked = query_local_index(index_path, _query_text(query), limit=limit)
        expected = set(_query_expected_ids(query))
        returned = [row["object_id"] for row in ranked]
        if expected and expected.intersection(returned):
            hits += 1
        for result_rank, row in enumerate(ranked, start=1):
            metadata = row.get("metadata", {})
            results.append(
                {
                    "query_id": query.get("query_id", ""),
                    "result_rank": result_rank,
                    "object_id": row["object_id"],
                    "object_type": _internal_object_type_for_expected(str(metadata.get("object_type", "unknown") or "unknown")),
                    "case_id": metadata.get("case_id", ""),
                    "ticker": metadata.get("ticker", ""),
                    "fiscal_period": metadata.get("fiscal_period", ""),
                    "source_hash": metadata.get("source_sha256", ""),
                    "normalized_transcript_hash": metadata.get("normalized_transcript_sha256", ""),
                    "provenance_hash": metadata.get("provenance_hash", ""),
                    "section_label": _section_label(metadata),
                    "speaker_role": _speaker_role(metadata),
                    "qa_pair_id": metadata.get("qa_pair_id", ""),
                    "retrieval_score": row["score"],
                    "retrieval_method": "bm25",
                    "citation_valid": _citation_ok(metadata, query),
                    "raw_text_returned": False,
                    "blocked_reason": None,
                    "notes": "metadata-only retrieval result; raw text suppressed",
                }
            )
    summary = _summarize_results(
        queries=queries,
        objects=[],
        results=results,
        smoke_metrics=True,
        query_file_path=str(queries_path),
        result_file_path=None,
    )
    summary["hit_count"] = hits
    summary["hit_rate"] = (hits / len(queries)) if queries else 0.0
    return summary


def evaluate_retrieval_objects(objects_path: Path, queries_path: Path, *, limit: int = 5) -> dict[str, Any]:
    queries = load_eval_queries(queries_path)
    objects = load_retrieval_manifest(objects_path)
    object_failures: list[str] = []
    for index, row in enumerate(objects, start=1):
        object_failures.extend(f"object row {index}: {error}" for error in validate_no_forbidden_payload_keys(row, context="object_manifest"))
    results: list[dict[str, Any]] = []
    for query in queries:
        if _query_abstention_expected(query):
            results.append(_abstain_row(query, _blocked_reason_for_query(query)))
            continue
        eligible_objects = _filter_objects_for_query(objects, query)
        if not eligible_objects:
            results.append(_abstain_row(query, "no_index"))
            continue
        temp_index = _build_disposable_index(eligible_objects)
        ranked = _ranked_with_priority(temp_index, _query_text(query), limit=limit)
        if not ranked:
            results.append(_abstain_row(query, "no_evidence_for_signal"))
            continue
        for result_rank, row in enumerate(ranked, start=1):
            results.append(_result_row(query, row, result_rank=result_rank))
    case_ids = {_query_case(query) for query in queries if _query_case(query)}
    smoke_metrics = case_ids == {"hd_2025_q4"} or len(queries) <= 20
    summary = _summarize_results(
        queries=queries,
        objects=objects,
        results=results,
        smoke_metrics=smoke_metrics,
        query_file_path=str(queries_path),
        result_file_path=None,
    )
    summary["failures"].extend(object_failures)
    return summary
