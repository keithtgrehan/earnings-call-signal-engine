from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_resource_registry.py"


def test_resource_registry_schema_requires_rights_fields() -> None:
    schema = json.loads((ROOT / "schemas" / "resource_registry.schema.json").read_text(encoding="utf-8"))
    required = set(schema["$defs"]["resource_record"]["required"])
    for field in (
        "source_id",
        "rights_tier",
        "allowed_commit",
        "commit_allowed",
        "raw_body_allowed",
        "metadata_only",
        "source_terms_checked",
        "robots_status",
        "provenance_hash",
        "blocked_reason",
    ):
        assert field in required


def test_public_domain_government_source_example_validates() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--path", "configs/resource_registry.example.yml"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = yaml.safe_load((ROOT / "configs" / "resource_registry.example.yml").read_text(encoding="utf-8"))
    sec = next(row for row in payload["resources"] if row["source_id"] == "sec_companyfacts_metadata")
    assert sec["rights_tier"] == "public_domain"
    assert "fair-access" in sec["license_or_terms_summary"]


def test_missing_rights_tier_fails_validation(tmp_path: Path) -> None:
    payload = yaml.safe_load((ROOT / "configs" / "resource_registry.example.yml").read_text(encoding="utf-8"))
    payload["resources"][0]["rights_tier"] = ""
    path = tmp_path / "bad.yml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--path", str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "missing or unclear rights_tier" in result.stdout


def test_unknown_rights_fail_closed(tmp_path: Path) -> None:
    payload = yaml.safe_load((ROOT / "configs" / "resource_registry.example.yml").read_text(encoding="utf-8"))
    payload["resources"][0]["rights_tier"] = "unknown"
    path = tmp_path / "unknown.yml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--path", str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "missing or unclear rights_tier" in result.stdout


def test_official_ir_and_fred_examples_require_terms_checks() -> None:
    payload = yaml.safe_load((ROOT / "configs" / "resource_registry.example.yml").read_text(encoding="utf-8"))
    by_id = {row["source_id"]: row for row in payload["resources"]}
    assert by_id["company_ir_terms_checked"]["robots_or_terms_checked"] is True
    assert by_id["company_ir_terms_checked"]["raw_body_allowed"] is False
    assert by_id["fred_series_terms_required"]["robots_or_terms_checked"] is True
    assert "series-level" in by_id["fred_series_terms_required"]["license_or_terms_summary"]
