#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from resource_registry_common import write_json
from signal_engine.llm.config import validate_llm_config_payload


def _load_payload(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("LLM config must be a YAML object.")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate optional LLM backend config without provider calls.")
    parser.add_argument("--path", default="configs/llm.example.yml")
    parser.add_argument("--require-disabled-default", action="store_true")
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)

    try:
        payload = _load_payload(Path(args.path))
        errors = validate_llm_config_payload(payload, require_disabled_default=args.require_disabled_default)
    except Exception as exc:
        errors = [str(exc)]

    summary = {"status": "valid" if not errors else "invalid", "errors": errors}
    if args.json_out:
        write_json(Path(args.json_out), summary)
    if errors:
        print(f"LLM config validation failed: {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    print("LLM config validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
