from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_source_license_record_schema_has_fail_closed_fields() -> None:
    schema = json.loads((ROOT / "schemas" / "source_license_record.schema.json").read_text(encoding="utf-8"))
    required = set(schema["required"])
    assert {
        "source_id",
        "source_url_or_path",
        "rights_tier",
        "license_or_terms_summary",
        "allowed_storage",
        "allowed_commit",
        "commit_allowed",
        "allowed_training_use",
        "training_allowed",
        "allowed_eval_use",
        "eval_allowed",
        "raw_body_allowed",
        "metadata_only",
        "robots_or_terms_checked",
        "source_terms_checked",
        "paywall_or_login_status",
        "robots_status",
        "provenance_hash",
        "reviewer_or_operator",
        "blocked_reason",
    }.issubset(required)
