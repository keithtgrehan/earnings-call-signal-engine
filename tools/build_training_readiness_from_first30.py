#!/usr/bin/env python3
"""Build a first30 training-readiness manifest without training."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_INGESTION = ROOT / "data" / "acquisition" / "first30_transcript_ingestion_manifest.csv"
DEFAULT_TRANSCRIPTS = ROOT / "data" / "corpus" / "manual_local_transcript_registry.csv"
DEFAULT_OUT = ROOT / "data" / "training" / "first30_training_readiness_manifest.csv"
REPORT_PATH = ROOT / "reports" / "acquisition" / "training_set_readiness_from_first30.md"

FIELDS = [
    "case_id",
    "ticker",
    "registered_transcript",
    "provenance_complete",
    "promotion_manifest_passed",
    "explicit_training_rights_ref",
    "training_allowed",
    "valid_adjudicated_labels",
    "status",
    "blocked_reason",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_training_readiness(
    *,
    ingestion_manifest: Path = DEFAULT_INGESTION,
    transcript_registry: Path = DEFAULT_TRANSCRIPTS,
    out_path: Path = DEFAULT_OUT,
) -> dict[str, Any]:
    ingestion_rows = {row.get("case_id", ""): row for row in read_csv(ingestion_manifest)}
    transcripts = {row.get("case_id", ""): row for row in read_csv(transcript_registry)}
    rows: list[dict[str, str]] = []
    for case_id, row in sorted(ingestion_rows.items()):
        if row.get("control_fixture") == "true":
            continue
        transcript = transcripts.get(case_id, {})
        provenance_complete = bool(transcript.get("sha256") and transcript.get("source_url") and transcript.get("provenance_path"))
        training_ref = row.get("explicit_training_rights_ref", "")
        blockers: list[str] = []
        if case_id not in transcripts:
            blockers.append("transcript_not_registered")
        if not provenance_complete:
            blockers.append("provenance_incomplete")
        if row.get("training_allowed") != "true" or not training_ref:
            blockers.append("explicit_training_rights_missing")
        blockers.append("valid_adjudicated_labels_below_100")
        rows.append(
            {
                "case_id": case_id,
                "ticker": row.get("ticker", ""),
                "registered_transcript": str(case_id in transcripts).lower(),
                "provenance_complete": str(provenance_complete).lower(),
                "promotion_manifest_passed": "true",
                "explicit_training_rights_ref": training_ref,
                "training_allowed": "false",
                "valid_adjudicated_labels": "0",
                "status": "NOT_READY",
                "blocked_reason": ";".join(sorted(set(blockers))),
            }
        )
    write_csv(out_path, rows, FIELDS)
    summary = {
        "rows": len(rows),
        "ready_rows": sum(1 for row in rows if row["status"] == "READY"),
        "status": "NOT_READY",
        "training_performed": False,
        "out_manifest": str(out_path),
    }
    write_report(summary, rows)
    return summary


def write_report(summary: dict[str, Any], rows: list[dict[str, str]]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    blockers: dict[str, int] = {}
    for row in rows:
        for reason in row.get("blocked_reason", "").split(";"):
            if reason:
                blockers[reason] = blockers.get(reason, 0) + 1
    lines = [
        "# Training Set Readiness From First30",
        "",
        f"- Status: `{summary['status']}`",
        f"- Manifest rows: {summary['rows']}",
        f"- Ready rows: {summary['ready_rows']}",
        "- Training performed: false",
        "- Weak/candidate labels promoted to gold: false",
        "- Minimum valid adjudicated labels required: 100",
        "- Explicit training rights required: true",
        "",
        "## Blockers",
        "",
    ]
    for reason, count in sorted(blockers.items()):
        lines.append(f"- `{reason}`: {count}")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build first30 training readiness report without training.")
    parser.add_argument("--ingestion-manifest", type=Path, default=DEFAULT_INGESTION)
    parser.add_argument("--transcript-registry", type=Path, default=DEFAULT_TRANSCRIPTS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    summary = build_training_readiness(ingestion_manifest=args.ingestion_manifest, transcript_registry=args.transcript_registry, out_path=args.out)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
