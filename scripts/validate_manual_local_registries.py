#!/usr/bin/env python3
"""Validate Desktop-only manual-local transcript/audio registries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.user_authorized_ingest_common import DEFAULT_WORKSPACE, file_sha256, is_relative_to, read_csv


def _validate_row(row: dict[str, str], *, workspace: Path, require_exists: bool) -> list[str]:
    errors: list[str] = []
    local_path = Path(row.get("local_path", ""))
    if not row.get("case_id"):
        errors.append("case_id is required")
    if not row.get("sha256"):
        errors.append("sha256 is required")
    if row.get("commit_allowed") != "false":
        errors.append("commit_allowed must be false")
    if row.get("training_allowed") != "false":
        errors.append("training_allowed must be false")
    if row.get("eval_allowed") == "true" and not row.get("approval_ref"):
        errors.append("eval_allowed=true requires approval_ref")
    if not row.get("source_url") and not row.get("provenance_path"):
        errors.append("source_url or provenance_path is required")
    if str(local_path) in {"", "."}:
        errors.append("local_path is required")
    else:
        if is_relative_to(local_path, ROOT):
            errors.append("raw local_path must not be inside the git repository")
        if require_exists and not local_path.exists():
            errors.append("local_path does not exist")
        if local_path.exists() and not is_relative_to(local_path, workspace):
            errors.append("local_path must be inside the configured Desktop workspace")
        if local_path.exists() and row.get("sha256") and file_sha256(local_path) != row.get("sha256"):
            errors.append("sha256 mismatch")
    return errors


def validate_registries(*, transcript_registry: Path, audio_registry: Path, workspace: Path, require_exists: bool) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    counts = {"transcript_rows": 0, "audio_rows": 0}
    for kind, path in (("transcript", transcript_registry), ("audio", audio_registry)):
        rows = read_csv(path)
        counts[f"{kind}_rows"] = len(rows)
        for index, row in enumerate(rows, start=2):
            errors = _validate_row(row, workspace=workspace, require_exists=require_exists)
            if errors:
                failures.append({"registry": str(path), "row": index, "case_id": row.get("case_id", ""), "errors": errors})
    return {"ok": not failures, **counts, "failures": failures}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate manual-local Desktop asset registries.")
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--transcript-registry", type=Path, default=ROOT / "data" / "corpus" / "manual_local_transcript_registry.csv")
    parser.add_argument("--audio-registry", type=Path, default=ROOT / "data" / "corpus" / "manual_local_audio_registry.csv")
    parser.add_argument("--allow-missing-files", action="store_true")
    args = parser.parse_args(argv)
    result = validate_registries(
        transcript_registry=args.transcript_registry,
        audio_registry=args.audio_registry,
        workspace=args.workspace,
        require_exists=not args.allow_missing_files,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
