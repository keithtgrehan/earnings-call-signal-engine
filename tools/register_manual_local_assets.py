#!/usr/bin/env python3
"""Register approved local transcript/audio assets as metadata without copying raw files."""

from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.source_rights_common import VENDOR_SOURCE_TYPES, as_bool, is_youtube_url, stable_hash, write_csv

DEFAULT_APPROVALS = ROOT / "data" / "acquisition" / "nyse_100_source_rights_review_queue.csv"
DEFAULT_OUT = ROOT / "data" / "acquisition" / "manual_local_asset_registry.csv"
DEFAULT_JSON_REPORT = ROOT / "reports" / "acquisition" / "manual_local_asset_registration.json"
DEFAULT_MD_REPORT = ROOT / "reports" / "acquisition" / "manual_local_asset_registration.md"
DOWNLOAD_ALLOWED_RIGHTS = {"safe_to_download", "rights_cleared", "manual_local_review_only"}
ASSET_TYPES = {"transcript", "audio"}
REGISTRY_FIELDS = [
    "record_id",
    "case_id",
    "ticker",
    "company_name",
    "asset_type",
    "source_type",
    "source_url",
    "local_path",
    "sha256",
    "bytes",
    "rights_status",
    "approval_ref",
    "approved_by",
    "approved_at",
    "license_config_ref",
    "allow_eval_use",
    "allow_training_use",
    "explicit_training_rights_ref",
    "raw_git_committed",
    "raw_file_copied_into_repo",
    "registered_at",
    "provenance_hash",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def read_approvals(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() in {".yml", ".yaml"}:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            rows = payload.get("approvals") or []
        elif isinstance(payload, list):
            rows = payload
        else:
            rows = []
        return [row for row in rows if isinstance(row, dict)]
    return read_csv(path)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def is_git_ignored(path: Path, repo_root: Path) -> bool:
    result = subprocess.run(["git", "check-ignore", "-q", str(path)], cwd=repo_root, check=False)
    return result.returncode == 0


def approval_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("case_id", "")).strip(),
        str(row.get("ticker", "") or row.get("ticker_symbol", "")).strip().upper(),
        str(row.get("asset_type", "")).strip(),
        str(row.get("source_url", "")).strip(),
    )


def build_approval_index(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    return {approval_key(row): row for row in rows}


def find_approval(index: dict[tuple[str, str, str, str], dict[str, Any]], mapping: dict[str, str]) -> dict[str, Any] | None:
    case_id = str(mapping.get("case_id", "")).strip()
    ticker = str(mapping.get("ticker", "") or mapping.get("ticker_symbol", "")).strip().upper()
    asset_type = str(mapping.get("asset_type", "")).strip()
    source_url = str(mapping.get("source_url", "")).strip()
    for key in ((case_id, ticker, asset_type, source_url), (case_id, ticker, asset_type, ""), (case_id, "", asset_type, source_url)):
        if key in index:
            return index[key]
    return None


def validate_registration_inputs(
    *,
    mapping: dict[str, str],
    approval: dict[str, Any] | None,
    local_path: Path,
    repo_root: Path,
    allowed_repo_local_root: Path | None,
) -> list[str]:
    errors: list[str] = []
    label = mapping.get("case_id") or mapping.get("local_path") or "<unknown>"
    for field in ("case_id", "ticker", "asset_type", "source_url", "local_path"):
        if not str(mapping.get(field, "")).strip():
            errors.append(f"{label}: {field} is required")
    asset_type = str(mapping.get("asset_type", "")).strip()
    if asset_type not in ASSET_TYPES:
        errors.append(f"{label}: asset_type must be transcript or audio")
    if as_bool(mapping.get("raw_git_committed")):
        errors.append(f"{label}: raw_git_committed=true is not allowed")
    if not local_path.exists() or not local_path.is_file():
        errors.append(f"{label}: local_path missing or not a file")
    if is_relative_to(local_path, repo_root):
        allowed = allowed_repo_local_root and is_relative_to(local_path, allowed_repo_local_root)
        if not allowed:
            errors.append(f"{label}: raw local_path is inside repo")
        elif not is_git_ignored(local_path, repo_root):
            errors.append(f"{label}: allowed repo-local path must be git-ignored")
    if approval is None:
        errors.append(f"{label}: matching approval row is required")
        return errors
    if not (as_bool(approval.get("allow_download")) or as_bool(approval.get("allow_eval_use"))):
        errors.append(f"{label}: approval must allow download or evaluation use")
    for field in ("approval_ref", "approved_by", "approved_at"):
        if not str(approval.get(field, "")).strip():
            errors.append(f"{label}: approval requires {field}")
    if approval.get("rights_status") not in DOWNLOAD_ALLOWED_RIGHTS:
        errors.append(f"{label}: approval rights_status is not permitted for local raw registration")
    if as_bool(approval.get("allow_training_use")) and not str(approval.get("explicit_training_rights_ref", "")).strip():
        errors.append(f"{label}: training use requires explicit_training_rights_ref")
    if is_youtube_url(str(approval.get("source_url") or mapping.get("source_url", ""))) and asset_type == "audio":
        errors.append(f"{label}: YouTube audio cannot be registered as approved local raw media")
    if approval.get("source_type") in VENDOR_SOURCE_TYPES and not str(approval.get("license_config_ref", "")).strip():
        errors.append(f"{label}: vendor raw registration requires license_config_ref")
    return errors


def register_assets(
    *,
    approvals_path: Path,
    path_map_path: Path,
    out_path: Path,
    json_report: Path,
    markdown_report: Path,
    repo_root: Path = ROOT,
    allowed_repo_local_root: Path | None = None,
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    approvals = build_approval_index(read_approvals(approvals_path))
    mappings = read_csv(path_map_path)
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    registered_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    for mapping in mappings:
        local_path = Path(str(mapping.get("local_path", ""))).expanduser()
        approval = find_approval(approvals, mapping)
        row_errors = validate_registration_inputs(
            mapping=mapping,
            approval=approval,
            local_path=local_path,
            repo_root=repo_root,
            allowed_repo_local_root=allowed_repo_local_root,
        )
        if row_errors:
            errors.extend(row_errors)
            continue
        assert approval is not None
        sha = file_sha256(local_path)
        row = {
            "record_id": stable_hash({"local_path": str(local_path), "sha256": sha})[:24].replace("sha256:", "manual_"),
            "case_id": mapping.get("case_id", ""),
            "ticker": str(mapping.get("ticker", "")).upper(),
            "company_name": approval.get("company_name", ""),
            "asset_type": mapping.get("asset_type", ""),
            "source_type": approval.get("source_type", "manual_local"),
            "source_url": mapping.get("source_url", ""),
            "local_path": str(local_path),
            "sha256": sha,
            "bytes": local_path.stat().st_size,
            "rights_status": approval.get("rights_status", ""),
            "approval_ref": approval.get("approval_ref", ""),
            "approved_by": approval.get("approved_by", ""),
            "approved_at": approval.get("approved_at", ""),
            "license_config_ref": approval.get("license_config_ref", ""),
            "allow_eval_use": str(as_bool(approval.get("allow_eval_use"))).lower(),
            "allow_training_use": str(as_bool(approval.get("allow_training_use"))).lower(),
            "explicit_training_rights_ref": approval.get("explicit_training_rights_ref", ""),
            "raw_git_committed": "false",
            "raw_file_copied_into_repo": "false",
            "registered_at": registered_at,
        }
        row["provenance_hash"] = stable_hash(row)
        rows.append(row)

    write_csv(out_path, rows, REGISTRY_FIELDS)
    summary = {
        "valid": not errors,
        "registered_rows": len(rows),
        "input_mappings": len(mappings),
        "raw_files_copied_into_repo": False,
        "raw_git_committed": False,
        "out": str(out_path),
    }
    write_reports(json_report=json_report, markdown_report=markdown_report, errors=errors, rows=rows, summary=summary)
    return rows, errors, summary


def write_reports(
    *,
    json_report: Path,
    markdown_report: Path,
    errors: list[str],
    rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    payload = {"valid": not errors, "errors": errors, "summary": summary, "records": rows}
    json_report.parent.mkdir(parents=True, exist_ok=True)
    json_report.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Manual Local Asset Registration",
        "",
        f"- Valid: {str(not errors).lower()}",
        f"- Registered rows: {len(rows)}",
        "- Raw files copied into repo: false",
        "- Raw git committed: false",
    ]
    if errors:
        lines.extend(["", "## Errors", *[f"- {error}" for error in errors]])
    markdown_report.parent.mkdir(parents=True, exist_ok=True)
    markdown_report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Register approved manual-local assets without copying raw files into the repo.")
    parser.add_argument("--approvals", type=Path, default=DEFAULT_APPROVALS)
    parser.add_argument("--path-map", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--json-report", type=Path, default=DEFAULT_JSON_REPORT)
    parser.add_argument("--markdown-report", type=Path, default=DEFAULT_MD_REPORT)
    parser.add_argument("--allowed-repo-local-root", type=Path)
    args = parser.parse_args(argv)
    rows, errors, summary = register_assets(
        approvals_path=args.approvals,
        path_map_path=args.path_map,
        out_path=args.out,
        json_report=args.json_report,
        markdown_report=args.markdown_report,
        allowed_repo_local_root=args.allowed_repo_local_root,
    )
    print(json.dumps({"valid": not errors, "errors": errors, "summary": summary, "registered_rows": len(rows)}, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
