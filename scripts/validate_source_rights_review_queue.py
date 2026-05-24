#!/usr/bin/env python3
"""Validate the NYSE 100 source-rights review queue guardrails."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.source_rights_common import QUEUE_FIELDS, VENDOR_SOURCE_TYPES, as_bool, is_youtube_url, read_csv


def validate_queue(path: Path) -> list[str]:
    errors: list[str] = []
    rows = read_csv(path)
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        prefix = f"row {index}"
        if list(row.keys()) != QUEUE_FIELDS:
            errors.append(f"{prefix}: invalid queue fields")
        source_id = row.get("source_id", "")
        if not source_id:
            errors.append(f"{prefix}: source_id is required")
        if source_id in seen:
            errors.append(f"{prefix}: duplicate source_id")
        seen.add(source_id)
        if not row.get("source_url"):
            errors.append(f"{prefix}: source_url is required")
        if as_bool(row.get("commit_allowed")):
            errors.append(f"{prefix}: commit_allowed must be false")
        if as_bool(row.get("allow_training_use")) and not row.get("explicit_training_rights_ref"):
            errors.append(f"{prefix}: allow_training_use requires explicit_training_rights_ref")
        if is_youtube_url(row.get("source_url", "")) and row.get("asset_type") in {"audio", "video", "video_metadata"}:
            errors.append(f"{prefix}: YouTube audio/video download is blocked")
        if row.get("source_type") in VENDOR_SOURCE_TYPES and as_bool(row.get("allow_download")) and not row.get("license_config_ref"):
            errors.append(f"{prefix}: vendor raw requires license_config_ref")
        if as_bool(row.get("allow_download")):
            for field in ("approval_ref", "approved_by", "approved_at"):
                if not row.get(field):
                    errors.append(f"{prefix}: approved download requires {field}")
        else:
            if row.get("manual_approval_required") != "true":
                errors.append(f"{prefix}: fail-closed rows must require manual approval")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate fail-closed source-rights review queue.")
    parser.add_argument("--queue", type=Path, default=ROOT / "data/acquisition/nyse_100_source_rights_review_queue.csv")
    args = parser.parse_args(argv)
    if not args.queue.exists():
        raise SystemExit(f"queue missing: {args.queue}")
    errors = validate_queue(args.queue)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"source-rights review queue validation passed: {args.queue} ({len(read_csv(args.queue))} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
