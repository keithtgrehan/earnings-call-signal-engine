from __future__ import annotations

import csv
from pathlib import Path

from tools.download_permitted_earnings_assets import download_from_manifest


FIELDNAMES = [
    "case_id",
    "ticker",
    "asset_type",
    "source_type",
    "source_url",
    "rights_status",
    "license_config_ref",
    "authorization_ref",
]


def _write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_download_guardrails_reject_unsafe_rows(tmp_path: Path) -> None:
    manifest = tmp_path / "permitted.csv"
    _write_manifest(
        manifest,
        [
            {
                "case_id": "jpm_2025_q4",
                "ticker": "JPM",
                "asset_type": "audio",
                "source_type": "youtube",
                "source_url": "https://youtube.com/watch?v=abc",
                "rights_status": "safe_to_download",
                "license_config_ref": "",
                "authorization_ref": "",
            },
            {
                "case_id": "bac_2025_q4",
                "ticker": "BAC",
                "asset_type": "transcript",
                "source_type": "official_ir",
                "source_url": "",
                "rights_status": "metadata_only",
                "license_config_ref": "",
                "authorization_ref": "",
            },
        ],
    )

    summary = download_from_manifest(workspace=tmp_path / "workspace", permitted_manifest=manifest)

    assert summary["downloaded"] == 0
    assert summary["rejected"] == 2
    assert any("YouTube" in error for error in summary["errors"])


def test_download_guardrails_allow_rights_cleared_file_url(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Operator: rights-cleared local transcript\n", encoding="utf-8")
    manifest = tmp_path / "permitted.csv"
    _write_manifest(
        manifest,
        [
            {
                "case_id": "jpm_2025_q4",
                "ticker": "JPM",
                "asset_type": "transcript",
                "source_type": "manually_approved_source",
                "source_url": source.as_uri(),
                "rights_status": "safe_to_download",
                "license_config_ref": "",
                "authorization_ref": "manual-test",
            }
        ],
    )

    summary = download_from_manifest(workspace=tmp_path / "workspace", permitted_manifest=manifest)

    assert summary["downloaded"] == 1
    downloaded = tmp_path / "workspace" / "_downloads" / "jpm_2025_q4" / "transcript" / "source.txt"
    assert downloaded.read_text(encoding="utf-8").startswith("Operator:")
