#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.agent5_acquisition import build_manual_local_registry, validate_manual_local_registry


def _load_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) if path.suffix.lower() in {".yml", ".yaml"} else json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("sources") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("manual local batch must be a list or object with sources list")
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _bool_value(value: Any, *, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _normalize_batch_row(row: dict[str, Any], *, operator: str) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    local_path = str(row.get("local_path") or row.get("source_path_ref") or "").strip()
    if not local_path:
        errors.append("missing local_path")
    elif not Path(local_path).exists():
        errors.append(f"local_path does not exist: {local_path}")
    source_type = str(row.get("source_type") or "manual_local").strip()
    if source_type != "manual_local":
        errors.append("source_type must be manual_local")
    if _bool_value(row.get("raw_file_copied_into_repo"), default=False):
        errors.append("raw_file_copied_into_repo must be false")
    if "eval_allowed" not in row:
        errors.append("eval_allowed must be explicit")
    rights_tier = str(row.get("rights_tier") or "unknown").strip()
    eval_allowed = _bool_value(row.get("eval_allowed"), default=False)
    training_allowed = _bool_value(row.get("training_allowed"), default=False)
    commit_allowed = _bool_value(row.get("commit_allowed"), default=False)
    if rights_tier in {"", "unknown", "restricted"} and (eval_allowed or training_allowed or commit_allowed):
        errors.append("unknown/restricted manual-local rights cannot allow commit/training/eval")
    source_url = str(row.get("source_url") or row.get("source_url_or_path") or "").strip()
    if (eval_allowed or training_allowed or commit_allowed) and not source_url:
        errors.append("source_url is required before enabling eval/training/commit")
    if errors:
        return None, errors
    normalized = {
        "case_id": row.get("case_id", ""),
        "ticker": row.get("ticker", ""),
        "source_path_ref": local_path,
        "media_type": row.get("media_type", "transcript"),
        "rights_tier": rights_tier,
        "source_url": source_url,
        "operator": row.get("operator") or operator,
        "raw_body_allowed": _bool_value(row.get("raw_body_allowed"), default=False),
        "raw_file_copied_into_repo": False,
        "commit_allowed": commit_allowed,
        "training_allowed": training_allowed,
        "eval_allowed": eval_allowed,
        "blocked_reason": row.get("blocked_reason")
        or row.get("notes")
        or "Manual local raw use requires rights review; file registered by path and hash only.",
    }
    return normalized, []


def load_batch_rows(path: Path) -> list[dict[str, Any]]:
    return _load_rows(path)


def register_batch_rows(rows: list[dict[str, Any]], *, operator: str = "manual_operator") -> tuple[list[dict[str, Any]], list[str]]:
    normalized_rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        normalized, row_errors = _normalize_batch_row(row, operator=operator)
        errors.extend(f"row {index}: {error}" for error in row_errors)
        if normalized:
            normalized_rows.append(normalized)
    if errors:
        return [], errors
    registered = build_manual_local_registry(normalized_rows, operator=operator)
    validation_errors = validate_manual_local_registry(registered)
    if validation_errors:
        return [], validation_errors
    return registered, []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Register manual-local transcript/audio/video paths by metadata and hash only.")
    parser.add_argument("--batch", default="data/review/staging/manual_local_batch.yml")
    parser.add_argument("--out", default="data/review/staging/manual_local_registry.jsonl")
    parser.add_argument("--operator", default="manual_operator")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    batch = Path(args.batch)
    if not batch.exists():
        print(f"Manual-local batch NOT_READY: {batch} is missing. No raw files copied.")
        return 0
    rows, errors = register_batch_rows(_load_rows(batch), operator=args.operator)
    if errors:
        print(f"Manual-local batch registration blocked: {len(errors)} error(s).")
        for error in errors:
            print(f"- {error}")
        return 1
    if not args.dry_run:
        _write_jsonl(Path(args.out), rows)
    print(f"Manual-local batch registration passed: {len(rows)} path/hash record(s), raw files not copied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
