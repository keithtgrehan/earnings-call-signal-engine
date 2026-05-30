#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.audio.registry import validate_audio_registry_row
from signal_engine.audio.schemas import validate_no_forbidden_audio_labels


def validate_registry(path: Path) -> dict[str, object]:
    rows: list[dict[str, str]] = []
    if path.exists():
        with path.open(newline="", encoding="utf-8") as handle:
            rows = [dict(row) for row in csv.DictReader(handle)]
    errors: list[dict[str, object]] = []
    for index, row in enumerate(rows, start=2):
        candidate = row.copy()
        candidate.setdefault("asset_type", "audio")
        candidate.setdefault("eval_allowed", candidate.get("eval_use_allowed", "false"))
        for error in validate_audio_registry_row(candidate, repo_root=ROOT) + validate_no_forbidden_audio_labels(row):
            errors.append({"row": index, "case_id": row.get("case_id", ""), "error": error})
        if row.get("raw_audio_committed") not in {"", "false"}:
            errors.append({"row": index, "case_id": row.get("case_id", ""), "error": "raw_audio_committed must be false"})
        if row.get("raw_asr_committed") not in {"", "false"}:
            errors.append({"row": index, "case_id": row.get("case_id", ""), "error": "raw_asr_committed must be false"})
    return {"rows": len(rows), "errors": errors}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate repo-safe audio registry metadata.")
    parser.add_argument("--registry", type=Path, default=ROOT / "data" / "acquisition" / "audio_registry.csv")
    args = parser.parse_args(argv)
    summary = validate_registry(args.registry)
    print(f"audio_registry rows={summary['rows']} errors={len(summary['errors'])}")
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
