from __future__ import annotations

from typing import Any

EXTERNAL_MODES = {"benchmark_only", "calibration_only"}
PROJECT_GOLD_SOURCE_ID = "project_human_gold_labels"


def validate_training_source_rows(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        for field in (
            "source_id",
            "source_type",
            "default_mode",
            "training_allowed",
            "writes_gold",
            "weak_labels_can_be_gold",
            "rights_status",
            "source_reference",
        ):
            if field not in row:
                errors.append(f"row {index}: missing required field {field}")
        external = row.get("source_type") in {"external_dataset", "benchmark_suite", "lexicon", "sec_metadata"}
        if external:
            if row.get("default_mode") not in EXTERNAL_MODES:
                errors.append(f"row {index}: external sources must default to benchmark_only or calibration_only")
            if row.get("training_allowed") is not False:
                errors.append(f"row {index}: external sources cannot allow training by default")
        if row.get("writes_gold") is not False:
            errors.append(f"row {index}: training sources cannot write gold labels")
        if row.get("weak_labels_can_be_gold") is not False:
            errors.append(f"row {index}: weak labels cannot become gold")
        if row.get("rights_status") in {"unknown", "restricted", ""} and row.get("training_allowed") is True:
            errors.append(f"row {index}: unknown or restricted rights block training")
    if not any(row.get("source_id") == PROJECT_GOLD_SOURCE_ID for row in rows):
        errors.append("project human gold labels must be represented as the only default supervised source")
    return errors


def build_training_candidate_manifest(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {
        "supervised_gold_candidates": [
            row for row in rows if row.get("source_id") == PROJECT_GOLD_SOURCE_ID and row.get("training_allowed") is True
        ],
        "benchmark_only_sources": [
            row for row in rows if row.get("default_mode") in {"benchmark_only", "calibration_only"}
        ],
        "blocked_sources": [
            row for row in rows if row.get("rights_status") in {"unknown", "restricted"} or row.get("training_allowed") is False
        ],
    }
