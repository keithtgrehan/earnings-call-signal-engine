#!/usr/bin/env python3
"""Validate public/local model-assist assets with fail-closed license gates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "data" / "review" / "public_model_assist_registry.example.yml"
REPORT_PATH = ROOT / "reports" / "review" / "public_model_assist_registry_validation.md"

REQUIRED_FIELDS = {
    "asset_id",
    "asset_type",
    "name",
    "source_url",
    "local_path",
    "license",
    "license_status",
    "permitted_uses",
    "blocked_reason",
    "requires_download",
    "download_performed",
    "raw_data_committed",
    "model_weights_committed",
    "notes",
}
ASSET_TYPES = {"model", "dataset", "lexicon"}
LICENSE_STATUSES = {"allowed", "research_only", "blocked", "unknown_fail_closed"}
PERMITTED_USES = {"weak_review_assist", "benchmark_only", "training", "redistribution"}
NONCOMMERCIAL_MARKERS = ("non-commercial", "noncommercial", "cc-by-nc", "cc by-nc", "cc-by-nc-", "cc by nc")


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value).split(",") if item.strip()]


def _rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        rows = payload.get("assets", [])
    else:
        rows = payload
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _is_unknown_license(row: dict[str, Any]) -> bool:
    license_text = str(row.get("license", "")).strip().lower()
    return not license_text or license_text in {"unknown", "not verified", "not_verified"} or row.get("license_status") == "unknown_fail_closed"


def _is_noncommercial(row: dict[str, Any]) -> bool:
    license_text = str(row.get("license", "")).strip().lower()
    return any(marker in license_text for marker in NONCOMMERCIAL_MARKERS)


def validate_registry_payload(payload: Any) -> dict[str, Any]:
    rows = _rows(payload)
    errors: list[str] = []
    asset_ids: list[str] = []
    allowed_weak_review_assist_assets: list[str] = []
    training_enabled_assets: list[str] = []
    download_performed = False
    raw_data_committed = False
    model_weights_committed = False

    if not rows:
        errors.append("registry has no assets")

    for index, row in enumerate(rows, start=1):
        asset_id = str(row.get("asset_id", "")).strip()
        asset_ids.append(asset_id)
        missing = sorted(field for field in REQUIRED_FIELDS if field not in row)
        if missing:
            errors.append(f"row {index} {asset_id or '<missing asset_id>'}: missing fields: {', '.join(missing)}")

        asset_type = str(row.get("asset_type", "")).strip()
        if asset_type not in ASSET_TYPES:
            errors.append(f"{asset_id or f'row {index}'}: invalid asset_type {asset_type!r}")

        license_status = str(row.get("license_status", "")).strip()
        if license_status not in LICENSE_STATUSES:
            errors.append(f"{asset_id or f'row {index}'}: invalid license_status {license_status!r}")

        permitted_uses = _as_list(row.get("permitted_uses"))
        invalid_uses = sorted(set(permitted_uses) - PERMITTED_USES)
        if invalid_uses:
            errors.append(f"{asset_id or f'row {index}'}: invalid permitted_uses: {', '.join(invalid_uses)}")

        if _is_unknown_license(row) and permitted_uses:
            errors.append(f"{asset_id}: unknown license must fail closed and cannot enable permitted_uses")
        if license_status == "blocked" and permitted_uses:
            errors.append(f"{asset_id}: blocked assets cannot enable permitted_uses")
        if "training" in permitted_uses and _is_noncommercial(row):
            errors.append(f"{asset_id}: non-commercial license cannot enable training")
        if "training" in permitted_uses and (
            license_status != "allowed" or not str(row.get("explicit_training_rights_ref", "")).strip()
        ):
            errors.append(f"{asset_id}: training requires license_status=allowed and explicit_training_rights_ref")

        requires_download = _as_bool(row.get("requires_download"))
        row_download_performed = _as_bool(row.get("download_performed"))
        if row_download_performed:
            download_performed = True
        if requires_download and row_download_performed and not str(row.get("explicit_local_download_approval_ref", "")).strip():
            errors.append(f"{asset_id}: download_performed=true requires explicit_local_download_approval_ref")

        if _as_bool(row.get("raw_data_committed")):
            raw_data_committed = True
            errors.append(f"{asset_id}: raw_data_committed=true is not allowed")
        if _as_bool(row.get("model_weights_committed")):
            model_weights_committed = True
            errors.append(f"{asset_id}: model_weights_committed=true is not allowed")

        if "weak_review_assist" in permitted_uses and license_status == "allowed":
            allowed_weak_review_assist_assets.append(asset_id)
        if "training" in permitted_uses:
            training_enabled_assets.append(asset_id)
        if license_status in {"blocked", "unknown_fail_closed", "research_only"} and not str(row.get("blocked_reason", "")).strip():
            errors.append(f"{asset_id}: blocked_reason is required unless license_status=allowed")

    duplicates = sorted(asset_id for asset_id in set(asset_ids) if asset_id and asset_ids.count(asset_id) > 1)
    for asset_id in duplicates:
        errors.append(f"{asset_id}: duplicate asset_id")

    return {
        "valid": not errors,
        "assets": len(rows),
        "error_count": len(errors),
        "errors": errors,
        "download_performed": download_performed,
        "raw_data_committed": raw_data_committed,
        "model_weights_committed": model_weights_committed,
        "allowed_weak_review_assist_assets": sorted(allowed_weak_review_assist_assets),
        "training_enabled_assets": sorted(training_enabled_assets),
        "final_adjudication_automated": False,
        "gold_labels_created": 0,
        "training_performed": False,
    }


def validate_registry(path: Path = DEFAULT_REGISTRY, report_path: Path = REPORT_PATH) -> dict[str, Any]:
    if not path.exists():
        summary = {
            "valid": False,
            "assets": 0,
            "error_count": 1,
            "errors": [f"registry missing: {path}"],
            "download_performed": False,
            "raw_data_committed": False,
            "model_weights_committed": False,
            "allowed_weak_review_assist_assets": [],
            "training_enabled_assets": [],
            "final_adjudication_automated": False,
            "gold_labels_created": 0,
            "training_performed": False,
        }
        write_report(summary, report_path)
        return summary
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    summary = validate_registry_payload(payload)
    write_report(summary, report_path)
    return summary


def write_report(summary: dict[str, Any], report_path: Path = REPORT_PATH) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Public Model Assist Registry Validation",
        "",
        f"- Valid: {str(summary['valid']).lower()}",
        f"- Assets registered: {summary['assets']}",
        f"- Error count: {summary['error_count']}",
        f"- Allowed weak-review-assist assets: {len(summary['allowed_weak_review_assist_assets'])}",
        f"- Training-enabled assets: {len(summary['training_enabled_assets'])}",
        f"- Downloads performed: {str(summary['download_performed']).lower()}",
        f"- Raw data committed: {str(summary['raw_data_committed']).lower()}",
        f"- Model weights committed: {str(summary['model_weights_committed']).lower()}",
        "- Final adjudication automated: false",
        "- Gold labels created: 0",
        "- Training performed: false",
        "",
        "## Errors",
        "",
    ]
    errors = summary.get("errors") or []
    lines.extend(f"- {error}" for error in errors) if errors else lines.append("- none")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate public/local model assist asset registry.")
    parser.add_argument("registry", nargs="?", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--out", type=Path, default=REPORT_PATH)
    args = parser.parse_args(argv)
    summary = validate_registry(args.registry, args.out)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
