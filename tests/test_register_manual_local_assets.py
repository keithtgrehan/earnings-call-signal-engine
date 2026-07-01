from __future__ import annotations

import csv
from pathlib import Path

from tools.register_manual_local_assets import REGISTRY_FIELDS, register_assets
from tools.source_rights_common import QUEUE_FIELDS


def _write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _approval(**overrides: str) -> dict[str, str]:
    row = {field: "" for field in QUEUE_FIELDS}
    row.update(
        {
            "case_id": "jpm_2025_q4",
            "ticker": "JPM",
            "company_name": "JPMorgan Chase & Co.",
            "asset_type": "transcript",
            "source_type": "official_ir",
            "source_url": "https://ir.example.com/transcript",
            "rights_status": "manual_local_review_only",
            "allow_download": "true",
            "allow_eval_use": "true",
            "allow_training_use": "false",
            "commit_allowed": "false",
            "approval_ref": "approval://jpm-q4",
            "approved_by": "Keith",
            "approved_at": "2026-05-28T00:00:00+00:00",
        }
    )
    row.update(overrides)
    return row


def _mapping(local_path: Path, **overrides: str) -> dict[str, str]:
    row = {
        "case_id": "jpm_2025_q4",
        "ticker": "JPM",
        "asset_type": "transcript",
        "source_url": "https://ir.example.com/transcript",
        "local_path": str(local_path),
        "raw_git_committed": "false",
    }
    row.update(overrides)
    return row


def test_registers_manual_local_asset_as_metadata_only(tmp_path: Path) -> None:
    local_file = tmp_path / "approved.txt"
    local_file.write_text("approved local transcript", encoding="utf-8")
    approvals = tmp_path / "approvals.csv"
    mappings = tmp_path / "paths.csv"
    out = tmp_path / "registry.csv"
    _write_csv(approvals, [_approval()], QUEUE_FIELDS)
    _write_csv(mappings, [_mapping(local_file)], ["case_id", "ticker", "asset_type", "source_url", "local_path", "raw_git_committed"])

    rows, errors, summary = register_assets(
        approvals_path=approvals,
        path_map_path=mappings,
        out_path=out,
        json_report=tmp_path / "report.json",
        markdown_report=tmp_path / "report.md",
        repo_root=tmp_path / "repo",
    )

    assert errors == []
    assert summary["registered_rows"] == 1
    assert rows[0]["sha256"].startswith("sha256:")
    assert rows[0]["raw_file_copied_into_repo"] == "false"
    with out.open(newline="", encoding="utf-8") as handle:
        assert list(csv.DictReader(handle))[0].keys() == set(REGISTRY_FIELDS)


def test_rejects_repo_local_raw_path_without_allowed_ignored_root(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    local_file = repo / "raw.txt"
    local_file.write_text("raw", encoding="utf-8")
    approvals = tmp_path / "approvals.csv"
    mappings = tmp_path / "paths.csv"
    _write_csv(approvals, [_approval()], QUEUE_FIELDS)
    _write_csv(mappings, [_mapping(local_file)], ["case_id", "ticker", "asset_type", "source_url", "local_path", "raw_git_committed"])

    _, errors, _ = register_assets(
        approvals_path=approvals,
        path_map_path=mappings,
        out_path=tmp_path / "registry.csv",
        json_report=tmp_path / "report.json",
        markdown_report=tmp_path / "report.md",
        repo_root=repo,
    )

    assert any("inside repo" in error for error in errors)


def test_rejects_raw_git_committed_true(tmp_path: Path) -> None:
    local_file = tmp_path / "approved.txt"
    local_file.write_text("approved local transcript", encoding="utf-8")
    approvals = tmp_path / "approvals.csv"
    mappings = tmp_path / "paths.csv"
    _write_csv(approvals, [_approval()], QUEUE_FIELDS)
    _write_csv(
        mappings,
        [_mapping(local_file, raw_git_committed="true")],
        ["case_id", "ticker", "asset_type", "source_url", "local_path", "raw_git_committed"],
    )

    _, errors, _ = register_assets(
        approvals_path=approvals,
        path_map_path=mappings,
        out_path=tmp_path / "registry.csv",
        json_report=tmp_path / "report.json",
        markdown_report=tmp_path / "report.md",
        repo_root=tmp_path / "repo",
    )

    assert any("raw_git_committed" in error for error in errors)
