#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from resource_registry_common import write_json

REQUIRED_FIELDS = {
    "provider_name",
    "model_slot",
    "secret_env_var_name",
    "max_cost_per_run",
    "timeout_seconds",
    "output_role",
    "log_cost",
    "log_latency",
}


def validate_config(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_FIELDS - set(payload))
    for field in missing:
        errors.append(f"missing required field {field}")
    if payload.get("output_role") not in {"reviewer", "candidate"}:
        errors.append("output_role must be reviewer or candidate")
    if str(payload.get("secret_env_var_name", "")).startswith(("sk-", "pk-")):
        errors.append("secret_env_var_name must be an environment variable name, not a secret value")
    try:
        if float(payload.get("max_cost_per_run", 0)) < 0:
            errors.append("max_cost_per_run must be non-negative")
    except (TypeError, ValueError):
        errors.append("max_cost_per_run must be numeric")
    try:
        if int(payload.get("timeout_seconds", 0)) <= 0:
            errors.append("timeout_seconds must be positive")
    except (TypeError, ValueError):
        errors.append("timeout_seconds must be an integer")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate BYOK reviewer config without provider calls.")
    parser.add_argument("--path", default="configs/byok_reviewer.example.yml")
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)

    try:
        payload = yaml.safe_load(Path(args.path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("BYOK config must be a YAML object.")
        errors = validate_config(payload)
    except Exception as exc:
        errors = [str(exc)]
    summary = {"status": "valid" if not errors else "invalid", "errors": errors}
    if args.json_out:
        write_json(Path(args.json_out), summary)
    if errors:
        print(f"BYOK reviewer config validation failed: {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    print("BYOK reviewer config validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
