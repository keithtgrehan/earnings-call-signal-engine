from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_ROOT = Path(__file__).resolve().parents[3] / "schemas"
OUTPUT_SCHEMAS = {
    "signal_candidates": "llm_signal_candidates.schema.json",
    "evidence_judge": "llm_evidence_judge.schema.json",
}


class LLMOutputValidationError(ValueError):
    pass


def _schema_for_output(output_type: str) -> dict[str, Any]:
    try:
        schema_name = OUTPUT_SCHEMAS[output_type]
    except KeyError as exc:
        raise LLMOutputValidationError(f"unsupported LLM output_type {output_type}") from exc
    return json.loads((SCHEMA_ROOT / schema_name).read_text(encoding="utf-8"))


def _type_matches(value: Any, expected_type: str) -> bool:
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return True


def _validate_schema(value: Any, schema: dict[str, Any], path: str, errors: list[str]) -> None:
    expected_type = schema.get("type")
    if isinstance(expected_type, str) and not _type_matches(value, expected_type):
        errors.append(f"{path} must be {expected_type}")
        return

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path} must be {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path} must be one of {schema['enum']}")

    if isinstance(value, str):
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(value.strip()) < min_length:
            errors.append(f"{path} must be a non-empty string")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if isinstance(minimum, (int, float)) and value < minimum:
            errors.append(f"{path} must be >= {minimum}")
        if isinstance(maximum, (int, float)) and value > maximum:
            errors.append(f"{path} must be <= {maximum}")

    if isinstance(value, list):
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(value) < min_items:
            errors.append(f"{path} must contain at least {min_items} item(s)")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate_schema(item, item_schema, f"{path}[{index}]", errors)

    if isinstance(value, dict):
        required = schema.get("required", [])
        if isinstance(required, list):
            for field in required:
                if field not in value:
                    errors.append(f"{path}.{field} is required")
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for field, field_value in value.items():
                if field in properties and isinstance(properties[field], dict):
                    _validate_schema(field_value, properties[field], f"{path}.{field}", errors)
                elif schema.get("additionalProperties") is False:
                    errors.append(f"{path}.{field} is not allowed")


def validate_output_payload(payload: dict[str, Any], *, output_type: str) -> dict[str, Any]:
    schema = _schema_for_output(output_type)
    errors: list[str] = []
    _validate_schema(payload, schema, "$", errors)
    if errors:
        raise LLMOutputValidationError("; ".join(errors))
    return payload


def parse_and_validate_output(text: str, *, output_type: str) -> dict[str, Any]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMOutputValidationError("LLM output must be valid JSON and failed closed.") from exc
    if not isinstance(payload, dict):
        raise LLMOutputValidationError("LLM output must be a JSON object.")
    return validate_output_payload(payload, output_type=output_type)
