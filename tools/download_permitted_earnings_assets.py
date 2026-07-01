#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.acquisition.nyse100 import copy_file_url_to_workspace, write_json
from signal_engine.acquisition.rights import validate_permitted_download_row


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def download_from_manifest(*, workspace: Path, permitted_manifest: Path) -> dict[str, object]:
    rows = _read_rows(permitted_manifest)
    errors: list[str] = []
    downloaded = 0
    rejected = 0
    for row in rows:
        row_errors = validate_permitted_download_row(row)
        if row_errors:
            rejected += 1
            errors.extend(f"{row.get('case_id', '<missing>')}: {error}" for error in row_errors)
            continue
        parsed = urlparse(row["source_url"])
        if parsed.scheme != "file":
            rejected += 1
            errors.append(f"{row.get('case_id', '<missing>')}: only file:// URLs are enabled in this local permitted-acquisition helper")
            continue
        source_name = Path(parsed.path).name
        destination = workspace / "_downloads" / row["case_id"] / row.get("asset_type", "transcript") / source_name
        copy_file_url_to_workspace(row["source_url"], destination)
        downloaded += 1
    summary = {"downloaded": downloaded, "rejected": rejected, "errors": errors}
    write_json(workspace / "_audit" / "permitted_download_acquisition_log.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Download only explicitly permitted earnings-call assets.")
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--permitted-manifest", type=Path, required=True)
    args = parser.parse_args()
    print(download_from_manifest(workspace=args.workspace, permitted_manifest=args.permitted_manifest))


if __name__ == "__main__":
    main()
