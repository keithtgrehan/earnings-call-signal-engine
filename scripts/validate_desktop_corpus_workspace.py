#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path


MEDIA_SUFFIXES = {".mp3", ".mp4", ".wav", ".m4a", ".mov", ".webm", ".mkv"}


def validate_workspace(workspace: Path) -> list[str]:
    errors: list[str] = []
    audit = workspace / "_audit" / "nyse_earnings_call_audit.csv"
    if not audit.exists():
        return [f"audit CSV missing: {audit}"]
    with audit.open(newline="", encoding="utf-8") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    for index, row in enumerate(rows, start=1):
        for field in ("transcript_local_path", "audio_local_path", "video_local_path"):
            path = Path(row[field])
            if not path.exists():
                errors.append(f"row {index}: missing {field}: {path}")
            if workspace not in path.resolve().parents:
                errors.append(f"row {index}: local path outside workspace: {path}")
        if row.get("rights_status") != "safe_to_download":
            for folder_field in ("audio_local_path", "video_local_path"):
                folder = Path(row[folder_field])
                if folder.exists():
                    for media in folder.iterdir():
                        if media.suffix.lower() in MEDIA_SUFFIXES:
                            errors.append(f"row {index}: media file exists without safe_to_download: {media}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    errors = validate_workspace(args.workspace)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Desktop corpus workspace validation passed: {args.workspace}")


if __name__ == "__main__":
    main()
