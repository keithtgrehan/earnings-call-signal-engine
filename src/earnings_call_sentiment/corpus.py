from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

CORPUS_ROOT = Path("data/corpus")

CORPUS_LAYOUT = {
    "root": CORPUS_ROOT,
    "manifests": CORPUS_ROOT / "manifests",
    "raw_root": CORPUS_ROOT / "raw",
    "raw_transcripts": CORPUS_ROOT / "raw" / "transcripts",
    "raw_audio": CORPUS_ROOT / "raw" / "audio",
    "raw_video": CORPUS_ROOT / "raw" / "video",
    "processed_root": CORPUS_ROOT / "processed",
    "processed_chunks": CORPUS_ROOT / "processed" / "chunks",
    "processed_evidence_objects": CORPUS_ROOT / "processed" / "evidence_objects",
    "processed_alignments": CORPUS_ROOT / "processed" / "alignments",
    "reports": CORPUS_ROOT / "reports",
    "retrieval": CORPUS_ROOT / "retrieval",
}

TRANSCRIPT_PARSE_STATUSES = {
    "timed_segments_available",
    "synthetic_segments_generated",
    "raw_text_only",
    "missing",
}

FETCH_STATUSES = {
    "verified_local",
    "derived_outputs_available",
    "source_page_only",
    "not_fetched",
    "not_available",
    "missing",
}

MANIFEST_COLUMNS = [
    "case_id",
    "company",
    "ticker",
    "fiscal_period",
    "event_date",
    "transcript_url",
    "transcript_local_path",
    "audio_url",
    "audio_local_path",
    "video_url",
    "video_local_path",
    "transcript_verified",
    "audio_verified",
    "video_verified",
    "transcript_source_type",
    "audio_source_type",
    "video_source_type",
    "transcript_parse_status",
    "audio_fetch_status",
    "video_fetch_status",
    "official_source_url",
    "official_source_type",
    "source_url",
    "origin_manifest_path",
    "notes",
    "provenance_json",
]


@dataclass(frozen=True)
class CorpusCase:
    case_id: str
    company: str
    ticker: str
    fiscal_period: str
    event_date: str
    transcript_url: str = ""
    transcript_local_path: str = ""
    audio_url: str = ""
    audio_local_path: str = ""
    video_url: str = ""
    video_local_path: str = ""
    transcript_verified: bool = False
    audio_verified: bool = False
    video_verified: bool = False
    transcript_source_type: str = ""
    audio_source_type: str = ""
    video_source_type: str = ""
    transcript_parse_status: str = "missing"
    audio_fetch_status: str = "missing"
    video_fetch_status: str = "missing"
    official_source_url: str = ""
    official_source_type: str = ""
    source_url: str = ""
    origin_manifest_path: str = ""
    notes: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_manifest_row(self) -> dict[str, str]:
        payload = asdict(self)
        payload["transcript_verified"] = _serialize_bool(self.transcript_verified)
        payload["audio_verified"] = _serialize_bool(self.audio_verified)
        payload["video_verified"] = _serialize_bool(self.video_verified)
        payload["provenance_json"] = json.dumps(self.provenance, sort_keys=True)
        payload.pop("provenance", None)
        return {column: str(payload.get(column, "") or "") for column in MANIFEST_COLUMNS}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def corpus_root() -> Path:
    return repo_root() / CORPUS_ROOT


def ensure_corpus_layout() -> dict[str, Path]:
    resolved: dict[str, Path] = {}
    root = repo_root()
    for key, relative in CORPUS_LAYOUT.items():
        path = root / relative
        path.mkdir(parents=True, exist_ok=True)
        resolved[key] = path
    return resolved


def _serialize_bool(value: bool) -> str:
    return "true" if bool(value) else "false"


def parse_bool(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def to_repo_relative(path: Path | None) -> str:
    if path is None:
        return ""
    resolved = path.expanduser().resolve()
    try:
        return str(resolved.relative_to(repo_root()))
    except ValueError:
        return str(resolved)


def resolve_repo_path(value: str | Path | None) -> Path | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    path = Path(text).expanduser()
    return path if path.is_absolute() else (repo_root() / path).resolve()


def write_manifest_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: str(row.get(column, "") or "") for column in MANIFEST_COLUMNS})
    return path


def write_manifest_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            payload = dict(row)
            provenance_json = str(payload.pop("provenance_json", "") or "").strip()
            if provenance_json:
                try:
                    payload["provenance"] = json.loads(provenance_json)
                except json.JSONDecodeError:
                    payload["provenance"] = {"raw": provenance_json}
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
    return path


def load_manifest_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def build_manifest_validation_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    seen_case_ids: set[str] = set()
    for index, row in enumerate(rows, start=1):
        case_id = str(row.get("case_id", "")).strip()
        prefix = f"row {index}"
        if not case_id:
            errors.append(f"{prefix} missing case_id")
            continue
        prefix = f"{case_id}"
        if case_id in seen_case_ids:
            errors.append(f"{prefix} duplicated in manifest")
        seen_case_ids.add(case_id)

        for required_field in ("company", "ticker", "fiscal_period", "event_date", "transcript_source_type"):
            if not str(row.get(required_field, "")).strip():
                errors.append(f"{prefix} missing {required_field}")

        if str(row.get("transcript_parse_status", "")) not in TRANSCRIPT_PARSE_STATUSES:
            errors.append(
                f"{prefix} invalid transcript_parse_status: {row.get('transcript_parse_status', '')}"
            )
        for status_field in ("audio_fetch_status", "video_fetch_status"):
            if str(row.get(status_field, "")) not in FETCH_STATUSES:
                errors.append(f"{prefix} invalid {status_field}: {row.get(status_field, '')}")

        for verified_field in ("transcript_verified", "audio_verified", "video_verified"):
            value = str(row.get(verified_field, "")).strip().lower()
            if value not in {"true", "false"}:
                errors.append(f"{prefix} invalid {verified_field}: {row.get(verified_field, '')}")

        for local_path_field in ("transcript_local_path", "audio_local_path", "video_local_path"):
            path = resolve_repo_path(row.get(local_path_field))
            if path is not None and not path.exists():
                errors.append(f"{prefix} missing local artifact: {local_path_field} -> {path}")

        transcript_verified = parse_bool(row.get("transcript_verified"))
        transcript_local_path = str(row.get("transcript_local_path", "")).strip()
        transcript_url = str(row.get("transcript_url", "")).strip()
        if transcript_verified and not (transcript_local_path or transcript_url):
            errors.append(f"{prefix} transcript_verified=true but no transcript path or URL was recorded")
        if transcript_verified and not transcript_local_path:
            warnings.append(f"{prefix} transcript_verified=true without a committed local transcript path")

        if parse_bool(row.get("audio_verified")) and not (
            str(row.get("audio_local_path", "")).strip()
            or str(row.get("audio_url", "")).strip()
        ):
            warnings.append(f"{prefix} audio_verified=true but no local path or URL was recorded")
        if parse_bool(row.get("video_verified")) and not (
            str(row.get("video_local_path", "")).strip()
            or str(row.get("video_url", "")).strip()
        ):
            warnings.append(f"{prefix} video_verified=true but no local path or URL was recorded")

        provenance_json = str(row.get("provenance_json", "")).strip()
        if not provenance_json:
            errors.append(f"{prefix} missing provenance_json")
        else:
            try:
                json.loads(provenance_json)
            except json.JSONDecodeError as exc:
                errors.append(f"{prefix} invalid provenance_json: {exc}")

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "case_count": len(rows),
        "transcript_verified_count": sum(parse_bool(row.get("transcript_verified")) for row in rows),
        "audio_verified_count": sum(parse_bool(row.get("audio_verified")) for row in rows),
        "video_verified_count": sum(parse_bool(row.get("video_verified")) for row in rows),
        "errors": errors,
        "warnings": warnings,
    }


def validate_manifest_csv(path: Path) -> dict[str, Any]:
    rows = load_manifest_csv(path)
    return build_manifest_validation_summary(rows)
