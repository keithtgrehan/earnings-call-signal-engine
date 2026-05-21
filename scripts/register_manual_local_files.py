#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from resource_registry_common import stable_provenance_hash, write_json

VALID_MEDIA_TYPES = {"transcript", "audio", "video"}


def build_registration_record(
    *,
    source_id: str,
    source_name: str,
    source_path: Path,
    media_type: str,
    rights_tier: str,
    license_or_terms_summary: str,
    reviewer_or_operator: str,
) -> dict[str, Any]:
    if media_type not in VALID_MEDIA_TYPES:
        raise ValueError(f"media_type must be one of {sorted(VALID_MEDIA_TYPES)}")
    now = datetime.now(UTC).isoformat()
    record = {
        "source_id": source_id,
        "source_name": source_name,
        "source_url_or_path": str(source_path),
        "source_type": "manual_local",
        "media_type": media_type,
        "rights_tier": rights_tier,
        "license_or_terms_summary": license_or_terms_summary,
        "operator_supplied": True,
        "registered_at": now,
        "retrieval_timestamp": now,
        "file_exists_at_registration": source_path.exists(),
        "file_size_bytes": source_path.stat().st_size if source_path.exists() else None,
        "raw_body_allowed": False,
        "raw_use_blocked": True,
        "raw_file_copied_into_repo": False,
        "allowed_storage": "metadata_only",
        "allowed_commit": False,
        "commit_allowed": False,
        "allowed_training_use": "no",
        "training_allowed": "no",
        "allowed_eval_use": "review_required",
        "eval_allowed": "review_required",
        "metadata_only": True,
        "acquisition_method": "manual_local_registration_no_copy",
        "robots_or_terms_checked": False,
        "source_terms_checked": False,
        "paywall_or_login_status": "operator_attestation_required",
        "robots_status": "not_applicable_manual_local",
        "last_checked_at": datetime.now(UTC).date().isoformat(),
        "reviewer_or_operator": reviewer_or_operator,
        "blocked_reason": "Manual local file registered as metadata only; raw use requires explicit rights review.",
        "notes": "The raw file content is not read, copied, or committed by this registration scaffold.",
    }
    record["provenance_hash"] = stable_provenance_hash(record)
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Register manual local transcript/audio/video file metadata without copying raw files.")
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--source-name", required=True)
    parser.add_argument("--source-path", required=True)
    parser.add_argument("--media-type", required=True, choices=sorted(VALID_MEDIA_TYPES))
    parser.add_argument("--rights-tier", default="manual_supplied")
    parser.add_argument("--terms-summary", default="Manual local source; operator attestation and terms review required before raw use.")
    parser.add_argument("--operator", default="unknown")
    parser.add_argument("--out", help="Optional JSON output path. If omitted, prints the record only.")
    args = parser.parse_args(argv)

    record = build_registration_record(
        source_id=args.source_id,
        source_name=args.source_name,
        source_path=Path(args.source_path),
        media_type=args.media_type,
        rights_tier=args.rights_tier,
        license_or_terms_summary=args.terms_summary,
        reviewer_or_operator=args.operator,
    )
    if args.out:
        write_json(Path(args.out), {"records": [record]})
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
