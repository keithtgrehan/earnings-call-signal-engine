#!/usr/bin/env python3
"""Register manually approved local audio files by path/hash only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.audio.registry import validate_audio_registry_row
from tools.user_authorized_ingest_common import AUDIO_REGISTRY_FIELDS, DEFAULT_WORKSPACE, file_sha256, is_relative_to, now_iso, read_csv, write_csv

DEFAULT_OUT = ROOT / "data" / "corpus" / "manual_local_audio_registry.csv"
REPORT_PATH = ROOT / "reports" / "acquisition" / "manual_local_audio_registration.md"


def register_local_audio(*, input_csv: Path | None, workspace: Path, out_path: Path = DEFAULT_OUT) -> dict[str, Any]:
    input_rows = read_csv(input_csv) if input_csv else []
    rows: list[dict[str, str]] = []
    failures: list[dict[str, Any]] = []
    for index, row in enumerate(input_rows, start=2):
        local_path = Path(row.get("local_path", ""))
        candidate = {
            "case_id": row.get("case_id", ""),
            "ticker": row.get("ticker", ""),
            "company_name": row.get("company_name", ""),
            "asset_type": "audio",
            "local_path": str(local_path),
            "sha256": file_sha256(local_path) if local_path.exists() else "",
            "source_url": row.get("source_url", ""),
            "provenance_path": row.get("provenance_path", ""),
            "rights_status": row.get("rights_status", "safe_to_download"),
            "eval_allowed": row.get("eval_allowed", "true"),
            "commit_allowed": "false",
            "training_allowed": "false",
            "approval_ref": row.get("approval_ref", ""),
            "registered_timestamp": now_iso(),
            "notes": "Manual-local audio registered by path and sha256 only; raw audio stays outside git.",
        }
        errors = validate_audio_registry_row(candidate, repo_root=ROOT)
        if not local_path.exists():
            errors.append("local_path does not exist")
        if local_path.exists() and not is_relative_to(local_path, workspace):
            errors.append("local_path must be inside Desktop workspace")
        if errors:
            failures.append({"row": index, "case_id": candidate["case_id"], "errors": errors})
            continue
        rows.append(candidate)
    write_csv(out_path, rows, AUDIO_REGISTRY_FIELDS)
    summary = {"input_rows": len(input_rows), "registered_audio": len(rows), "failures": failures, "out": str(out_path)}
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        "# Manual-Local Audio Registration\n\n"
        f"- Input rows: {summary['input_rows']}\n"
        f"- Registered audio: {summary['registered_audio']}\n"
        f"- Failures: {len(failures)}\n"
        "- Raw audio committed: false\n",
        encoding="utf-8",
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Register local audio files by path/hash metadata only.")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    print(json.dumps(register_local_audio(input_csv=args.input, workspace=args.workspace, out_path=args.out), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
