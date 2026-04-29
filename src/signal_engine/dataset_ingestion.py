from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .domains import SUPPORTED_DOMAINS
from .text_emotion_baseline import EMOTION_LABELS

_REQUIRED_MANIFEST_FIELDS = {
    "dataset_id",
    "name",
    "modality",
    "task",
    "source_type",
    "file_paths",
    "labels",
    "license",
    "pii_status",
    "intended_use",
    "limitations",
}


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"JSONL file not found: {file_path}")
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        file_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        stripped = line.strip()
        if not stripped:
            continue
        item = json.loads(stripped)
        if not isinstance(item, dict):
            raise ValueError(
                f"Expected JSON object on line {line_number} in {file_path}."
            )
        records.append(item)
    return records


def validate_emotion_fixture_record(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("Emotion fixture record must be a JSON object.")

    required_fields = {"case_id", "domain", "text", "gold_label", "allowed_labels"}
    missing = sorted(required_fields - set(record))
    if missing:
        raise ValueError(
            f"Emotion fixture record missing required fields: {', '.join(missing)}."
        )

    domain = str(record["domain"]).strip()
    if domain not in SUPPORTED_DOMAINS:
        raise ValueError(
            f"Unsupported fixture domain '{domain}'. Expected one of {SUPPORTED_DOMAINS}."
        )

    text = str(record["text"]).strip()
    if not text:
        raise ValueError("Emotion fixture record text must not be empty.")

    gold_label = str(record["gold_label"]).strip()
    if gold_label not in EMOTION_LABELS:
        raise ValueError(
            f"Unsupported gold_label '{gold_label}'. Expected one of {EMOTION_LABELS}."
        )

    raw_allowed_labels = record["allowed_labels"]
    if not isinstance(raw_allowed_labels, list) or not raw_allowed_labels:
        raise ValueError("allowed_labels must be a non-empty list.")
    allowed_labels = [str(label).strip() for label in raw_allowed_labels if str(label).strip()]
    if len(allowed_labels) != len(raw_allowed_labels):
        raise ValueError("allowed_labels must not contain blank values.")
    invalid_labels = sorted(set(allowed_labels) - set(EMOTION_LABELS))
    if invalid_labels:
        raise ValueError(
            f"allowed_labels contains unsupported labels: {', '.join(invalid_labels)}."
        )
    if gold_label not in allowed_labels:
        raise ValueError(
            f"gold_label '{gold_label}' must be included in allowed_labels."
        )

    return {
        "case_id": str(record["case_id"]).strip(),
        "domain": domain,
        "text": text,
        "gold_label": gold_label,
        "allowed_labels": allowed_labels,
    }


def validate_dataset_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        raise ValueError("Dataset manifest must be a JSON object.")

    missing = sorted(_REQUIRED_MANIFEST_FIELDS - set(manifest))
    if missing:
        raise ValueError(f"Dataset manifest missing required fields: {', '.join(missing)}.")

    if manifest["source_type"] != "handcrafted_fixture":
        raise ValueError("This ingestion layer currently supports source_type='handcrafted_fixture' only.")

    labels = manifest["labels"]
    if not isinstance(labels, list) or not labels:
        raise ValueError("Manifest labels must be a non-empty list.")
    normalized_labels = [str(label).strip() for label in labels if str(label).strip()]
    if set(normalized_labels) != set(EMOTION_LABELS):
        raise ValueError(
            f"Manifest labels must match the supported emotion label set: {EMOTION_LABELS}."
        )

    raw_paths = manifest["file_paths"]
    if not isinstance(raw_paths, list) or not raw_paths:
        raise ValueError("Manifest file_paths must be a non-empty list.")

    base_dir = Path.cwd()
    if manifest.get("_manifest_path"):
        base_dir = Path(str(manifest["_manifest_path"])).resolve().parent

    resolved_paths: list[str] = []
    for raw_path in raw_paths:
        candidate = str(raw_path).strip()
        if not candidate:
            raise ValueError("Manifest file_paths must not contain blank values.")
        if candidate.startswith(("http://", "https://", "s3://", "gs://")):
            raise ValueError(
                f"Manifest file_paths must reference local files only: {candidate}"
            )
        file_path = (base_dir / candidate).resolve() if not Path(candidate).is_absolute() else Path(candidate).resolve()
        if not file_path.exists():
            raise ValueError(f"Manifest file does not exist: {file_path}")
        resolved_paths.append(str(file_path))

        if file_path.suffix.lower() == ".jsonl":
            for record in load_jsonl(file_path):
                validated = validate_emotion_fixture_record(record)
                if set(validated["allowed_labels"]) - set(normalized_labels):
                    raise ValueError(
                        f"Fixture {validated['case_id']} contains labels not present in the manifest."
                    )

    return {
        **manifest,
        "labels": normalized_labels,
        "file_paths": [str(path) for path in raw_paths],
        "resolved_file_paths": resolved_paths,
    }


def build_dataset_card_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    validated_manifest = validate_dataset_manifest(manifest)
    record_count = 0
    file_summaries: list[dict[str, Any]] = []
    for path_string in validated_manifest["resolved_file_paths"]:
        file_path = Path(path_string)
        rows = load_jsonl(file_path) if file_path.suffix.lower() == ".jsonl" else []
        record_count += len(rows)
        file_summaries.append(
            {
                "path": str(file_path),
                "size_bytes": file_path.stat().st_size,
                "record_count": len(rows),
            }
        )
    return {
        "dataset_id": validated_manifest["dataset_id"],
        "name": validated_manifest["name"],
        "source_type": validated_manifest["source_type"],
        "pii_status": validated_manifest["pii_status"],
        "labels": validated_manifest["labels"],
        "record_count": record_count,
        "files": file_summaries,
        "intended_use": validated_manifest["intended_use"],
        "limitations": validated_manifest["limitations"],
    }


__all__ = [
    "build_dataset_card_summary",
    "load_jsonl",
    "validate_dataset_manifest",
    "validate_emotion_fixture_record",
]
