#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


def validate_opik_config(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != "opik_observability.v1":
        errors.append("schema_version must be opik_observability.v1")
    opik = payload.get("opik")
    if not isinstance(opik, dict):
        return errors + ["missing opik object"]
    if opik.get("enabled") is not False:
        errors.append("opik.enabled must default to false")
    if opik.get("allow_network") is not False:
        errors.append("opik.allow_network must default to false")
    for field in ("api_key_env", "workspace_env", "project_name"):
        if field not in opik:
            errors.append(f"missing opik.{field}")
    api_key_env = str(opik.get("api_key_env", "") or "")
    if api_key_env.startswith(("sk-", "pk-", "ak-")):
        errors.append("opik.api_key_env must name an environment variable, not contain a key")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate optional Opik config without network calls.")
    parser.add_argument("--path", default="configs/opik.example.yml")
    args = parser.parse_args(argv)

    try:
        payload = yaml.safe_load(Path(args.path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Opik config must be a YAML object.")
        errors = validate_opik_config(payload)
    except Exception as exc:
        errors = [str(exc)]
    if errors:
        print(f"Opik config validation failed: {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Opik config validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
