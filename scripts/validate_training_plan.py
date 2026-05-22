#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from resource_registry_common import normalize_resource_rows, read_structured, validate_resource_rows, write_json
from signal_engine.training import build_training_readiness_summary
from validate_gold_labels import build_summary as build_gold_summary


def _resolve_repo_path(path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else ROOT / path


def build_summary(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Training plan must be a YAML object.")
    gold_summary: dict[str, Any]
    gold_path = _resolve_repo_path(str(payload.get("gold_label_path", "")))
    try:
        gold_summary = build_gold_summary(gold_path)
    except Exception as exc:
        gold_summary = {"status": "invalid", "path": str(gold_path), "row_count": 0, "errors": [str(exc)]}
    rights_path = _resolve_repo_path(str(payload.get("rights_registry_path", "")))
    try:
        rights_rows = normalize_resource_rows(read_structured(rights_path))
        rights_errors = validate_resource_rows(rights_rows)
    except Exception as exc:
        rights_errors = [str(exc)]
    summary = build_training_readiness_summary(payload=payload, gold_summary=gold_summary, rights_errors=rights_errors)
    summary["path"] = str(path)
    summary["gold_errors"] = gold_summary.get("errors", [])
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Signal Engine training plan without training models.")
    parser.add_argument("--path", default="configs/training_plan.example.yml")
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)

    try:
        summary = build_summary(Path(args.path))
    except Exception as exc:
        summary = {"status": "invalid", "path": args.path, "plan_errors": [str(exc)], "readiness_blockers": []}

    if args.json_out:
        write_json(Path(args.json_out), summary)

    if summary["status"] == "invalid":
        print(f"Training plan validation failed: {len(summary.get('plan_errors', []))} error(s).")
        for error in summary.get("plan_errors", []):
            print(f"- {error}")
        return 1
    if summary["status"] == "not_ready":
        print("Training plan validation passed with status NOT_READY.")
        for blocker in summary.get("readiness_blockers", []):
            print(f"- {blocker}")
        return 0
    print("Training plan validation passed with status READY.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
