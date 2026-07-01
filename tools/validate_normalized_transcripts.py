#!/usr/bin/env python3
"""Validate normalized transcript manifests without reading raw body text into git."""

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

from tools.normalize_registered_transcripts import DEFAULT_OUT
from tools.user_authorized_ingest_common import is_relative_to, read_csv


def validate_normalized_manifest(path: Path = DEFAULT_OUT) -> dict[str, Any]:
    rows = read_csv(path)
    failures: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=2):
        row_failures: list[str] = []
        if row.get("raw_text_committed") != "false":
            row_failures.append("raw_text_committed must be false")
        if not row.get("raw_sha256", "").startswith("sha256:"):
            row_failures.append("raw_sha256 is required")
        normalized_path = Path(row.get("normalized_local_path", ""))
        if is_relative_to(normalized_path, ROOT):
            row_failures.append("normalized transcript JSON must stay outside git")
        if normalized_path.exists():
            payload = json.loads(normalized_path.read_text(encoding="utf-8"))
            if payload.get("raw_text_committed") is not False:
                row_failures.append("normalized JSON raw_text_committed must be false")
            forbidden = {"raw_text", "transcript_text", "body", "content", "excerpt"}
            present = forbidden.intersection(payload)
            if present:
                row_failures.append("normalized JSON contains raw-body field(s): " + ",".join(sorted(present)))
        if row_failures:
            failures.append({"row": index, "case_id": row.get("case_id", ""), "errors": row_failures})
    return {"ok": not failures, "rows": len(rows), "failures": failures}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate normalized transcript manifest rows.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    result = validate_normalized_manifest(args.manifest)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
