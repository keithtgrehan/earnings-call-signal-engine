#!/usr/bin/env python3
"""Validate affective research model/dataset registries.

The validator is intentionally policy-heavy and dependency-light. It checks the
example YAML registries directly and fails closed on unsupported affective,
biometric, dating, finance, and workplace/education claims.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


REQUIRED_FIELDS = [
    "name",
    "modality",
    "task",
    "license",
    "allowed_use",
    "benchmark_only_default",
    "training_allowed",
    "raw_data_allowed",
    "sensitive_biometric_risk",
    "workplace_education_prohibited_use",
    "signal_engine_relevance",
    "dating_app_relevance",
    "evidence_provenance_requirements",
    "failure_modes",
    "legal_notes",
    "source_url",
]

BOOLEAN_FIELDS = [
    "benchmark_only_default",
    "training_allowed",
    "raw_data_allowed",
    "sensitive_biometric_risk",
    "workplace_education_prohibited_use",
]

MODALITIES = {"text", "audio", "video", "multimodal"}
NOT_RELEVANT = {"not_relevant", "not relevant", "none", "n/a", "na"}
PREFIX_BLOCK_MARKERS = [
    "no",
    "not",
    "never",
    "must not",
    "does not",
    "without",
]
SUFFIX_BLOCK_MARKERS = [
    "blocked",
    "prohibited",
    "forbidden",
]


def load_registry(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = yaml.safe_load(fh)
    if not isinstance(payload, dict):
        raise ValueError("registry must be a YAML mapping")
    return payload


def combined_text(entry: dict[str, Any]) -> str:
    return " ".join(str(value) for value in entry.values()).lower()


def is_relevant(value: Any) -> bool:
    text = str(value).strip().lower()
    return bool(text) and text not in NOT_RELEVANT


def phrase_occurrence_is_blocked(text: str, index: int, phrase: str) -> bool:
    prefix = text[max(0, index - 32): index].strip(" ;,.-")
    suffix = text[index + len(phrase): index + len(phrase) + 40]
    return any(prefix.endswith(marker) for marker in PREFIX_BLOCK_MARKERS) or any(
        marker in suffix for marker in SUFFIX_BLOCK_MARKERS
    )


def has_blocked_phrase(text: str, phrase: str) -> bool:
    phrase = phrase.lower()
    start = 0
    while True:
        index = text.find(phrase, start)
        if index == -1:
            return False
        if phrase_occurrence_is_blocked(text, index, phrase):
            return True
        start = index + len(phrase)


def has_unblocked_phrase(text: str, phrase: str) -> bool:
    phrase = phrase.lower()
    start = 0
    while True:
        index = text.find(phrase, start)
        if index == -1:
            return False
        if not phrase_occurrence_is_blocked(text, index, phrase):
            return True
        start = index + len(phrase)


def add_error(errors: list[str], path: Path, row: int, name: str, message: str) -> None:
    errors.append(f"{path}: entry {row} ({name}): {message}")


def validate_entry(path: Path, row: int, entry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    name = str(entry.get("name", "<missing name>"))

    for field in REQUIRED_FIELDS:
        value = entry.get(field)
        if value is None or value == "":
            add_error(errors, path, row, name, f"required field is empty: {field}")

    for field in BOOLEAN_FIELDS:
        if field in entry and not isinstance(entry[field], bool):
            add_error(errors, path, row, name, f"field must be boolean: {field}")

    modality = entry.get("modality")
    if modality not in MODALITIES:
        add_error(errors, path, row, name, f"invalid modality: {modality}")

    text = combined_text(entry)
    source_url = str(entry.get("source_url", ""))
    external = source_url.startswith(("http://", "https://"))

    if external and entry.get("benchmark_only_default") is not True:
        add_error(errors, path, row, name, "external entries must be benchmark_only_default=true")

    if entry.get("training_allowed") is not False:
        if "explicit license review" not in text or "rights record" not in text:
            add_error(
                errors,
                path,
                row,
                name,
                "training_allowed must stay false unless explicit license review and rights record are documented",
            )

    if entry.get("raw_data_allowed") is not False:
        if "explicit rights record" not in text:
            add_error(errors, path, row, name, "raw_data_allowed must stay false unless an explicit rights record is documented")

    if entry.get("workplace_education_prohibited_use") is not True:
        add_error(errors, path, row, name, "workplace/education emotion inference must be blocked")

    for phrase in [
        "workplace/education emotion inference",
        "deception detection",
        "biometric identity inference",
    ]:
        if not has_blocked_phrase(text, phrase):
            add_error(errors, path, row, name, f"blocked-use note missing for {phrase}")
        if has_unblocked_phrase(text, phrase):
            add_error(errors, path, row, name, f"unblocked prohibited phrase found: {phrase}")

    if not (
        has_blocked_phrase(text, "true internal emotion inference")
        or has_blocked_phrase(text, "true emotion inference")
    ):
        add_error(errors, path, row, name, "entry must block true internal emotion inference")
    if has_unblocked_phrase(text, "true internal emotion inference") or has_unblocked_phrase(text, "true emotion inference"):
        add_error(errors, path, row, name, "entry may not claim true internal emotion inference")

    if is_relevant(entry.get("dating_app_relevance")):
        for required in ["opt-in", "consent", "privacy"]:
            if required not in text:
                add_error(errors, path, row, name, f"dating relevance must require {required}")

    if is_relevant(entry.get("signal_engine_relevance")):
        if "no trading" not in text:
            add_error(errors, path, row, name, "finance relevance must block trading claims")
        if "alpha" not in text:
            add_error(errors, path, row, name, "finance relevance must block alpha claims")

    visual_or_body = modality in {"video", "multimodal"} or "body-language" in text or "pose" in text or "gaze" in text
    if visual_or_body and "observable cues only" not in text:
        add_error(errors, path, row, name, "video/body-language outputs must be framed as observable cues only")

    return errors


def validate_registry(path: Path) -> dict[str, Any]:
    payload = load_registry(path)
    errors: list[str] = []
    entries = payload.get("entries")

    if not payload.get("registry_version"):
        errors.append(f"{path}: registry_version is required")
    if not isinstance(entries, list) or not entries:
        errors.append(f"{path}: entries must be a non-empty list")
        entries = []

    for row, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            errors.append(f"{path}: entry {row}: entry must be a mapping")
            continue
        errors.extend(validate_entry(path, row, entry))

    return {
        "status": "valid" if not errors else "invalid",
        "path": str(path),
        "row_count": len(entries),
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate affective research registries.")
    parser.add_argument("--path", required=True, help="Path to an affective registry YAML file.")
    parser.add_argument("--json-out", help="Optional path for JSON validation summary.")
    args = parser.parse_args(argv)

    try:
        summary = validate_registry(Path(args.path))
    except Exception as exc:
        summary = {
            "status": "invalid",
            "path": args.path,
            "row_count": 0,
            "errors": [str(exc)],
        }

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    if summary["errors"]:
        print(f"Affective registry validation failed: {summary['row_count']} row(s), {len(summary['errors'])} error(s).")
        for error in summary["errors"]:
            print(f"- {error}")
        return 1

    print(f"Affective registry validation passed: {summary['row_count']} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
