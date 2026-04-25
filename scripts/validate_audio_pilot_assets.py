#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return []
        return [{key: (value or "").strip() for key, value in row.items()} for row in reader]


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in {"true", "yes", "y", "1"}


def _parse_optional_float(value: str, *, field_name: str, row_id: str) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"Invalid {field_name} '{value}' for row {row_id}") from exc


def evaluate_audio_assets(rows: list[dict[str, str]], *, intake_path: Path) -> dict[str, Any]:
    if not rows:
        return {
            "status": "blocked",
            "input_path": str(intake_path),
            "reason": "No audio intake CSV is available yet.",
            "usable_case_ids": [],
            "invalid_rows": [],
        }

    usable_case_ids: list[str] = []
    invalid_rows: list[dict[str, str]] = []
    for row in rows:
        row_id = row.get("id", "")
        audio_path = row.get("audio_file_to_add", "")
        if not audio_path:
            continue
        start_seconds = _parse_optional_float(row.get("audio_start_seconds", ""), field_name="audio_start_seconds", row_id=row_id)
        end_seconds = _parse_optional_float(row.get("audio_end_seconds", ""), field_name="audio_end_seconds", row_id=row_id)
        path = Path(audio_path)
        reasons: list[str] = []
        if not path.exists():
            reasons.append("audio path does not exist")
        if end_seconds is not None and start_seconds is None:
            reasons.append("end time provided without start time")
        if start_seconds is not None and end_seconds is not None and end_seconds <= start_seconds:
            reasons.append("audio_end_seconds must be greater than audio_start_seconds")
        if not _is_truthy(row.get("audio_rights_confirmed", "")):
            reasons.append("audio_rights_confirmed is not approved")
        if reasons:
            invalid_rows.append({"id": row_id, "audio_file_to_add": audio_path, "reasons": "; ".join(reasons)})
            continue
        usable_case_ids.append(row_id)

    if not usable_case_ids:
        return {
            "status": "blocked",
            "input_path": str(intake_path),
            "reason": "No aligned approved audio assets are available yet.",
            "usable_case_ids": [],
            "invalid_rows": invalid_rows,
        }
    return {
        "status": "ready_for_audio_feature_extraction",
        "input_path": str(intake_path),
        "reason": "",
        "usable_case_ids": usable_case_ids,
        "invalid_rows": invalid_rows,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Audio Pilot Asset Status",
        "",
        f"- status: `{payload['status']}`",
        "",
    ]
    if payload["status"] != "ready_for_audio_feature_extraction":
        lines.extend(
            [
                "## Current State",
                "",
                payload["reason"],
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Usable Cases",
                "",
            ]
        )
        for case_id in payload["usable_case_ids"]:
            lines.append(f"- `{case_id}`")
        lines.append("")
    lines.extend(
        [
            "## Invalid Rows",
            "",
        ]
    )
    if payload["invalid_rows"]:
        for row in payload["invalid_rows"]:
            lines.append(f"- `{row['id']}`: {row['reasons']}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate whether the audio pilot intake sheet contains any usable approved assets."
    )
    parser.add_argument(
        "--input-csv",
        default=str(ROOT / "data" / "multimodal_research" / "audio_pilot_intake.csv"),
        help="Path to the audio pilot intake CSV.",
    )
    parser.add_argument(
        "--status-out",
        default=str(ROOT / "data" / "multimodal_research" / "audio_pilot_asset_status.json"),
        help="Path to the audio asset status JSON output.",
    )
    parser.add_argument(
        "--report-out",
        default=str(ROOT / "docs" / "audio-pilot-asset-status.md"),
        help="Path to the audio asset status Markdown output.",
    )
    args = parser.parse_args(argv)

    input_csv = Path(args.input_csv)
    payload = evaluate_audio_assets(_read_rows(input_csv), intake_path=input_csv)
    _write_json(Path(args.status_out), payload)
    report_out = Path(args.report_out)
    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(_render_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "usable_case_count": len(payload["usable_case_ids"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
