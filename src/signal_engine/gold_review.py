from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
import hashlib
import json
import re
from pathlib import Path
from typing import Any

GOLD_REQUIRED_FIELDS = {
    "case_id",
    "label_id",
    "signal_type",
    "direction",
    "speaker_role",
    "evidence_text",
    "reviewer",
    "reviewed_at",
    "source_file",
    "provenance_hash",
}

VALID_SIGNAL_TYPES = {
    "guidance_revision",
    "analyst_pressure",
    "management_hedging",
    "uncertainty",
    "opportunity_commitment",
    "risk_friction",
    "neutral",
    "neutral/no_signal",
    "reassurance",
    "answer_shift",
}

BLOCKING_STATUSES = {
    "BLOCKED_CONTAMINATION_RISK",
    "BLOCKED_EXTERNAL_SOURCE",
    "BLOCKED_NO_PROVENANCE",
    "BLOCKED_DUPLICATE",
}


def load_jsonl_with_errors(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    if not path.exists():
        return rows, [{"line_number": 0, "error": f"{path} does not exist"}]
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append({"line_number": line_number, "error": str(exc), "raw_line_hash": _text_hash(line)})
            continue
        if not isinstance(row, dict):
            errors.append({"line_number": line_number, "error": "expected JSON object", "raw_line_hash": _text_hash(line)})
            continue
        row["_line_number"] = line_number
        rows.append(row)
    return rows, errors


def _text_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_evidence(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def classify_gold_row(row: dict[str, Any], *, duplicate_label: bool = False) -> tuple[str, list[str]]:
    reasons: list[str] = []
    missing = sorted(field for field in GOLD_REQUIRED_FIELDS if not str(row.get(field, "")).strip())
    if duplicate_label:
        return "BLOCKED_DUPLICATE", ["duplicate label_id"]
    if row.get("source_type") == "external_dataset":
        return "BLOCKED_EXTERNAL_SOURCE", ["external_dataset source_type cannot be canonical gold"]
    if row.get("weak_label_only") is True or "weak_label_only" in row.get("contamination_flags", []):
        return "BLOCKED_CONTAMINATION_RISK", ["weak_label_only contamination flag"]
    unresolved = [flag for flag in row.get("contamination_flags", []) if str(flag).startswith("unresolved")]
    if unresolved:
        return "BLOCKED_CONTAMINATION_RISK", [f"unresolved contamination flag: {flag}" for flag in unresolved]
    if not str(row.get("provenance_hash", "")).startswith("sha256:"):
        return "BLOCKED_NO_PROVENANCE", ["missing sha256 provenance_hash"]
    if "evidence_text" in missing or not _normalize_evidence(str(row.get("evidence_text", ""))):
        return "REPAIRABLE_REVIEW_REQUIRED", ["evidence_text is empty"]
    if "reviewer" in missing or "reviewed_at" in missing:
        return "REPAIRABLE_REVIEW_REQUIRED", ["reviewer and reviewed_at are required"]
    if "source_file" in missing:
        return "REPAIRABLE_REVIEW_REQUIRED", ["source_file is required"]
    if missing:
        return "REPAIRABLE_SCHEMA_ONLY", [f"missing required field {field}" for field in missing]
    if row.get("signal_type") not in VALID_SIGNAL_TYPES:
        reasons.append(f"invalid signal_type {row.get('signal_type')!r}")
    if reasons:
        return "REPAIRABLE_SCHEMA_ONLY", reasons
    return "VALID", []


def audit_gold_labels(path: Path) -> dict[str, Any]:
    rows, parse_errors = load_jsonl_with_errors(path)
    label_counts = Counter(str(row.get("label_id", "")) for row in rows if str(row.get("label_id", "")).strip())
    audited: list[dict[str, Any]] = []
    for row in rows:
        duplicate_label = bool(row.get("label_id")) and label_counts[str(row.get("label_id"))] > 1
        status, reasons = classify_gold_row(row, duplicate_label=duplicate_label)
        audited.append({"status": status, "reasons": reasons, "row": row})
    for parse_error in parse_errors:
        audited.append({"status": "REPAIRABLE_SCHEMA_ONLY", "reasons": [parse_error["error"]], "row": parse_error})
    counts = Counter(item["status"] for item in audited)
    return {
        "source_path": str(path),
        "generated_at": datetime.now(UTC).isoformat(),
        "row_count": len(rows),
        "parse_error_count": len(parse_errors),
        "status_counts": dict(sorted(counts.items())),
        "valid_count": counts.get("VALID", 0),
        "audited": audited,
        "canonical_gold_modified": False,
    }


def write_gold_audit_outputs(summary: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    public_summary = {key: value for key, value in summary.items() if key != "audited"}
    (out_dir / "gold_label_audit.json").write_text(json.dumps(public_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Gold Label Audit",
        "",
        "This audit is read-only. It does not modify `data/gold/gold_labels.jsonl`.",
        "",
        f"- Source path: `{summary['source_path']}`",
        f"- Rows read: `{summary['row_count']}`",
        f"- Valid rows: `{summary['valid_count']}`",
        f"- Parse errors: `{summary['parse_error_count']}`",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in summary["status_counts"].items():
        lines.append(f"- `{status}`: `{count}`")
    (out_dir / "gold_label_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    buckets = {
        "valid_gold_labels.jsonl": {"VALID"},
        "invalid_gold_labels.jsonl": set(BLOCKING_STATUSES) | {"REPAIRABLE_SCHEMA_ONLY", "REPAIRABLE_REVIEW_REQUIRED"},
        "repairable_gold_labels.jsonl": {"REPAIRABLE_SCHEMA_ONLY", "REPAIRABLE_REVIEW_REQUIRED"},
        "blocked_gold_labels.jsonl": set(BLOCKING_STATUSES),
    }
    for filename, statuses in buckets.items():
        with (out_dir / filename).open("w", encoding="utf-8") as handle:
            for item in summary["audited"]:
                if item["status"] in statuses:
                    row = {key: value for key, value in item["row"].items() if not key.startswith("_")}
                    handle.write(json.dumps({"audit_status": item["status"], "audit_reasons": item["reasons"], **row}, sort_keys=True) + "\n")


def parse_review_packet(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    records: list[dict[str, Any]] = []
    current_case = "unknown_case"
    blocks: list[tuple[str, str, str]] = []
    current_candidate = ""
    current_lines: list[str] = []
    for line in text.splitlines():
        case_match = re.match(r"^##\s+(.+?)\s*$", line)
        candidate_match = re.match(r"^###\s+(.+?)\s*$", line)
        if candidate_match:
            if current_candidate:
                blocks.append((current_case, current_candidate, "\n".join(current_lines)))
            current_candidate = candidate_match.group(1).strip()
            current_lines = []
            continue
        if case_match and not line.startswith("###"):
            if current_candidate:
                blocks.append((current_case, current_candidate, "\n".join(current_lines)))
                current_candidate = ""
                current_lines = []
            current_case = case_match.group(1).split()[0].strip() or "unknown_case"
            continue
        if current_candidate:
            current_lines.append(line)
    if current_candidate:
        blocks.append((current_case, current_candidate, "\n".join(current_lines)))

    for index, (case_id, candidate_id, block) in enumerate(blocks, start=1):
        suggested_label = _field(block, "suggested_label") or _field(block, "predicted_label") or _field(block, "label")
        evidence_text = _field(block, "evidence_text") or _field(block, "evidence") or _field(block, "text")
        if not suggested_label and not evidence_text:
            continue
        record = {
            "candidate_id": _field(block, "candidate_id") or candidate_id or f"{path.stem}_{index:03d}",
            "case_id": _field(block, "case_id") or _field(block, "case") or case_id,
            "suggested_label": suggested_label or "unknown",
            "suggested_confidence": _field(block, "suggested_confidence") or _field(block, "confidence") or "unknown",
            "reason": _field(block, "reason") or "",
            "source_file": _field(block, "source_file") or _field(block, "source") or str(path),
            "note": _field(block, "note") or "",
            "evidence_text": evidence_text,
            "machine_suggestion_only": True,
            "gold_status": "not_gold",
            "review_status": "pending_human_review",
            "contamination_flags": ["machine_candidate_only", "not_gold"],
            "packet_path": str(path),
        }
        record["provenance_hash"] = _text_hash("|".join([record["case_id"], record["source_file"], record["evidence_text"]]))
        records.append(record)
    return records


def _field(text: str, name: str) -> str:
    pattern = rf"(?im)^\s*(?:[-*]\s*)?{re.escape(name)}\s*[:=]\s*(.+?)\s*$"
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip().strip("`")
    return ""


def build_first_100_queue(packet_paths: list[Path], *, limit: int = 100) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pool: list[dict[str, Any]] = []
    for path in packet_paths:
        if path.exists():
            pool.extend(parse_review_packet(path))
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for record in pool:
        key = (str(record.get("case_id", "")), _normalize_evidence(str(record.get("evidence_text", ""))))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(record)
    return deduped, deduped[:limit]


def validate_promotion_rows(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen_label_ids: set[str] = set()
    seen_provenance: set[str] = set()
    for index, row in enumerate(rows, start=1):
        for field in (
            "label_id",
            "case_id",
            "final_label",
            "review_status",
            "gold_status",
            "reviewer",
            "reviewed_at",
            "evidence_text",
            "source_file",
            "provenance_hash",
        ):
            if not str(row.get(field, "")).strip():
                errors.append(f"row {index}: missing required field {field}")
        if row.get("review_status") not in {"reviewed", "adjudicated"}:
            errors.append(f"row {index}: review_status must be reviewed/adjudicated")
        if row.get("gold_status") != "promotion_candidate":
            errors.append(f"row {index}: gold_status must be promotion_candidate")
        if row.get("source_type") == "external_dataset":
            errors.append(f"row {index}: external_dataset records cannot be promoted to gold")
        flags = set(row.get("contamination_flags") or [])
        if "weak_label_only" in flags or row.get("weak_label_only") is True:
            errors.append(f"row {index}: weak_label_only records cannot be promoted")
        unresolved = sorted(flag for flag in flags if str(flag).startswith("unresolved"))
        if unresolved:
            errors.append(f"row {index}: unresolved contamination flags {unresolved}")
        if row.get("machine_suggestion_only") is True and not str(row.get("human_final_label", "")).strip():
            errors.append(f"row {index}: machine suggestion requires human_final_label before promotion")
        label_id = str(row.get("label_id", "")).strip()
        if label_id:
            if label_id in seen_label_ids:
                errors.append(f"row {index}: duplicate label_id {label_id}")
            seen_label_ids.add(label_id)
        provenance_hash = str(row.get("provenance_hash", "")).strip()
        if provenance_hash:
            if provenance_hash in seen_provenance:
                errors.append(f"row {index}: duplicate provenance_hash {provenance_hash}")
            seen_provenance.add(provenance_hash)
            if not provenance_hash.startswith("sha256:"):
                errors.append(f"row {index}: provenance_hash must be sha256-prefixed")
    return errors


def summarize_review_metrics(queue_rows: list[dict[str, Any]], promotion_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    statuses = Counter(str(row.get("review_status", "unknown")) for row in queue_rows)
    labels = Counter(str(row.get("suggested_label", "unknown")) for row in queue_rows)
    promotion_rows = promotion_rows or []
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "queue_size": len(queue_rows),
        "review_status_counts": dict(sorted(statuses.items())),
        "suggested_label_counts": dict(sorted(labels.items())),
        "promotion_candidate_count": sum(1 for row in promotion_rows if row.get("gold_status") == "promotion_candidate"),
        "canonical_gold_modified": False,
    }
