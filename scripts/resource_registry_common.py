from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


RIGHTS_TIERS = {
    "public_domain",
    "publicly_available",
    "official_public_terms_checked",
    "open_licensed",
    "licensed",
    "manual_supplied",
    "restricted",
    "unknown",
}

SOURCE_TYPES = {
    "sec_edgar",
    "company_ir",
    "youtube_metadata",
    "licensed_vendor",
    "macro_fred",
    "manual_local",
    "external_dataset",
    "transcript_vendor",
    "research_dataset",
    "synthetic_fixture",
}

ALLOWED_USE_VALUES = {"yes", "no", "review_required", "benchmark_only", "retrieval_only"}
ALLOWED_STORAGE_VALUES = {"metadata_only", "raw_allowed_local_only", "raw_allowed_commit", "blocked"}

REQUIRED_RIGHTS_FIELDS = (
    "source_id",
    "source_name",
    "source_url_or_path",
    "source_type",
    "rights_tier",
    "license_or_terms_summary",
    "allowed_storage",
    "allowed_commit",
    "commit_allowed",
    "allowed_training_use",
    "training_allowed",
    "allowed_eval_use",
    "eval_allowed",
    "raw_body_allowed",
    "metadata_only",
    "acquisition_method",
    "robots_or_terms_checked",
    "source_terms_checked",
    "paywall_or_login_status",
    "robots_status",
    "provenance_hash",
    "last_checked_at",
    "reviewer_or_operator",
    "blocked_reason",
    "notes",
)

RESTRICTED_PATH_MARKERS = (
    "raw/transcript.txt",
    "raw_calls/",
    "raw/audio/",
    "raw/video/",
    "/audio/",
    "/video/",
    "transcript",
    "webcast",
    "earnings-call",
    "vendor",
    "seeking_alpha",
    "motley_fool",
    "paywall",
    "login",
    "subscription",
)

RAW_BODY_SUFFIXES = {
    ".txt",
    ".md",
    ".html",
    ".htm",
    ".pdf",
    ".mp3",
    ".mp4",
    ".wav",
    ".m4a",
    ".mov",
    ".vtt",
    ".srt",
    ".aac",
    ".flac",
    ".mkv",
    ".webm",
}


def read_structured(path: Path) -> Any:
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix in {".yml", ".yaml"}:
        return yaml.safe_load(text)
    if suffix == ".json":
        return json.loads(text)
    raise ValueError(f"Unsupported structured file extension: {path.suffix}")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def normalize_resource_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = payload.get("resources") or payload.get("records") or payload.get("sources")
    else:
        rows = None
    if not isinstance(rows, list):
        raise ValueError("Resource registry must be a list or an object with resources/records/sources.")
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError("Every resource registry row must be an object.")
    return rows


def stable_provenance_hash(record: dict[str, Any]) -> str:
    payload = {
        "source_id": record.get("source_id", ""),
        "source_name": record.get("source_name", ""),
        "source_url_or_path": record.get("source_url_or_path", ""),
        "source_type": record.get("source_type", ""),
        "rights_tier": record.get("rights_tier", ""),
        "license_or_terms_summary": record.get("license_or_terms_summary", ""),
        "last_checked_at": record.get("last_checked_at", ""),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def coerce_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    return None


def explicit_bool(row: dict[str, Any], primary: str, alias: str | None = None) -> bool | None:
    if primary in row:
        return coerce_bool(row.get(primary))
    if alias and alias in row:
        return coerce_bool(row.get(alias))
    return None


def explicit_use(row: dict[str, Any], primary: str, alias: str | None = None) -> str | None:
    if primary in row:
        return str(row.get(primary, "")).strip()
    if alias and alias in row:
        return str(row.get(alias, "")).strip()
    return None


def validate_resource_rows(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        for field in REQUIRED_RIGHTS_FIELDS:
            if field not in row:
                errors.append(f"row {index}: missing required field {field}")

        source_id = str(row.get("source_id", "")).strip()
        if not source_id:
            errors.append(f"row {index}: source_id is required")
        elif source_id in seen:
            errors.append(f"row {index}: duplicate source_id {source_id!r}")
        seen.add(source_id)

        rights_tier = str(row.get("rights_tier", "")).strip()
        if rights_tier not in RIGHTS_TIERS or rights_tier == "unknown":
            errors.append(f"row {index}: missing or unclear rights_tier {rights_tier!r}")

        source_type = str(row.get("source_type", "")).strip()
        if source_type and source_type not in SOURCE_TYPES:
            errors.append(f"row {index}: invalid source_type {source_type!r}")

        allowed_storage = str(row.get("allowed_storage", "")).strip()
        if allowed_storage not in ALLOWED_STORAGE_VALUES:
            errors.append(f"row {index}: unclear allowed_storage {allowed_storage!r}")

        for field, alias in (
            ("allowed_training_use", "training_allowed"),
            ("allowed_eval_use", "eval_allowed"),
        ):
            value = explicit_use(row, field, alias)
            if value not in ALLOWED_USE_VALUES:
                errors.append(f"row {index}: unclear {field} {value!r}")

        for field, alias in (
            ("allowed_commit", "commit_allowed"),
            ("raw_body_allowed", None),
            ("metadata_only", None),
            ("robots_or_terms_checked", "source_terms_checked"),
        ):
            if explicit_bool(row, field, alias) is None:
                errors.append(f"row {index}: invalid boolean {field} {row.get(field)!r}")

        if "paywall_or_login_status" not in row or not str(row.get("paywall_or_login_status", "")).strip():
            errors.append(f"row {index}: paywall_or_login_status must be represented")
        if "robots_status" not in row or not str(row.get("robots_status", "")).strip():
            errors.append(f"row {index}: robots_status must be represented")

        provenance_hash = str(row.get("provenance_hash", "")).strip()
        if not provenance_hash or provenance_hash in {"pending", "unknown", "todo"}:
            errors.append(f"row {index}: missing provenance_hash")

        license_summary = str(row.get("license_or_terms_summary", "")).strip().lower()
        if not license_summary or license_summary in {"unknown", "todo", "tbd"}:
            errors.append(f"row {index}: missing license_or_terms_summary")

        restricted = rights_tier == "restricted" or source_type in {"transcript_vendor", "licensed_vendor"}
        raw_body_allowed = explicit_bool(row, "raw_body_allowed") is True
        allowed_commit = explicit_bool(row, "allowed_commit", "commit_allowed") is True
        metadata_only = explicit_bool(row, "metadata_only") is True
        source_terms_checked = explicit_bool(row, "robots_or_terms_checked", "source_terms_checked") is True
        training_allowed = explicit_use(row, "allowed_training_use", "training_allowed")
        eval_allowed = explicit_use(row, "allowed_eval_use", "eval_allowed")

        if rights_tier in {"unknown", "publicly_available"} and raw_body_allowed:
            errors.append(f"row {index}: unknown or publicly_available rights cannot allow raw_body_allowed")
        if restricted and (raw_body_allowed or allowed_commit or allowed_storage == "raw_allowed_commit"):
            errors.append(f"row {index}: restricted source creates raw-body commit risk")
        if restricted and (training_allowed != "no" or eval_allowed != "no"):
            errors.append(f"row {index}: restricted source cannot allow training or evaluation use by default")
        if source_type == "youtube_metadata" and raw_body_allowed:
            errors.append(f"row {index}: YouTube metadata source cannot allow raw audio/video by default")
        if metadata_only and raw_body_allowed:
            errors.append(f"row {index}: metadata_only cannot also allow raw_body_allowed")
        if raw_body_allowed and not source_terms_checked:
            errors.append(f"row {index}: raw_body_allowed requires source_terms_checked")
        if allowed_commit and not raw_body_allowed and allowed_storage != "metadata_only":
            errors.append(f"row {index}: allowed_commit is unclear without raw_body_allowed or metadata_only")
        if allowed_commit and rights_tier in {"licensed", "manual_supplied"} and "commit" not in license_summary:
            errors.append(f"row {index}: commit permission for {rights_tier} must be explicit in license_or_terms_summary")
    return errors


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{path}: line {line_number}: expected JSON object")
        rows.append(row)
    return rows


def load_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def looks_like_restricted_artifact(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    suffix = Path(normalized).suffix
    return suffix in RAW_BODY_SUFFIXES and any(marker in normalized for marker in RESTRICTED_PATH_MARKERS)
