#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.ir_sec_acquisition import build_asset_availability, read_yaml, write_text


FIELDNAMES = [
    "case_id",
    "ticker",
    "fiscal_period",
    "event_identity_status",
    "transcript_status",
    "audio_status",
    "video_status",
    "slides_status",
    "official_ir_candidate",
    "sec_candidate",
    "manual_local_registered",
    "permitted_ingest_available",
    "rights_status",
    "blocked_reason_code",
    "manual_action",
    "provenance_complete",
]


def _load_rows(path: Path, keys: tuple[str, ...]) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = read_yaml(path)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in keys:
            rows = payload.get(key)
            if isinstance(rows, list):
                return rows
    return []


def build_availability_rows(availability: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case_id in sorted(availability):
        row = dict(availability[case_id])
        if not row.get("blocked_reason_code") and not row.get("permitted_ingest_available"):
            row["blocked_reason_code"] = "source_terms_not_checked" if row.get("official_ir_candidate") else "sec_metadata_only"
        if not row.get("manual_action") and not row.get("permitted_ingest_available"):
            row["manual_action"] = "review source rights and register manual-local path/hash if raw use is needed"
        rows.append({field: row.get(field, "") for field in FIELDNAMES})
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_report(rows: list[dict[str, Any]]) -> str:
    permitted = sum(1 for row in rows if row.get("permitted_ingest_available") is True)
    official = sum(1 for row in rows if row.get("official_ir_candidate") is True)
    sec = sum(1 for row in rows if row.get("sec_candidate") is True)
    manual = sum(1 for row in rows if row.get("manual_local_registered") is True)
    return f"""# IR/SEC Availability Matrix

Status: metadata-only availability report.

- Matrix rows: {len(rows)}
- Official IR candidate rows represented: {official}
- SEC metadata candidate rows represented: {sec}
- Manual-local registered rows represented: {manual}
- Permitted ingest rows represented: {permitted}
- Network used: no
- Raw assets written: no

Default result: source candidates are visible for coverage planning, but permitted ingest remains unavailable until explicit rights review and approval/config references exist.
"""


def _universe_record(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": event.get("case_id", ""),
        "ticker": event.get("ticker", ""),
        "fiscal_period": event.get("fiscal_period", ""),
        "event_identity_status": event.get("event_identity_status", "target_only"),
        "transcript_status": "not_collected_metadata_only",
        "audio_status": "not_collected_metadata_only",
        "video_status": "not_collected_metadata_only",
        "slides_status": "not_collected_metadata_only",
        "official_ir_candidate": False,
        "sec_candidate": False,
        "exhibit_candidate": False,
        "manual_local_registered": False,
        "permitted_ingest_available": False,
        "rights_status": event.get("rights_status", "unknown"),
        "blocked_reason_code": "source_terms_not_checked",
        "manual_action": "review source rights and register manual-local path/hash if raw use is needed",
        "provenance_complete": False,
    }


def _apply_official_ir_ticker_candidates(availability: dict[str, dict[str, Any]], official_rows: list[dict[str, Any]]) -> None:
    official_tickers = {str(row.get("ticker", "")).upper() for row in official_rows if row.get("ticker")}
    for record in availability.values():
        if str(record.get("ticker", "")).upper() not in official_tickers:
            continue
        record["official_ir_candidate"] = True
        if record.get("event_identity_status") == "target_only":
            record["event_identity_status"] = "source_candidate_found"
        if record.get("transcript_status") == "not_collected_metadata_only":
            record["transcript_status"] = "official_ir_candidate_rights_pending"
        if record.get("slides_status") == "not_collected_metadata_only":
            record["slides_status"] = "official_ir_candidate_rights_pending"
        if not record.get("blocked_reason_code"):
            record["blocked_reason_code"] = "source_terms_not_checked"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the IR/SEC source availability matrix.")
    parser.add_argument("--universe", default="data/corpus/nyse_5y_ir_sec_universe.yml")
    parser.add_argument("--official-ir", default="data/corpus/official_ir_candidate_map.yml")
    parser.add_argument("--sec-queue", default="data/corpus/sec_metadata_queue.yml")
    parser.add_argument("--manual-local", default="data/corpus/manual_local_registry.yml")
    parser.add_argument("--source-discovery", default="data/corpus/source_discovery_queue.yml")
    parser.add_argument("--out-csv", default="reports/agent5/ir_sec_availability_matrix.csv")
    parser.add_argument("--report", default="reports/agent5/ir_sec_availability_matrix.md")
    args = parser.parse_args(argv)

    official_rows = _load_rows(ROOT / args.official_ir, ("candidates",))
    candidates = [
        *_load_rows(ROOT / args.sec_queue, ("queue", "candidates")),
        *_load_rows(ROOT / args.manual_local, ("registered", "candidates", "rows")),
        *_load_rows(ROOT / args.source_discovery, ("candidates", "queue", "rows")),
    ]
    availability = build_asset_availability(candidates)
    for event in _load_rows(ROOT / args.universe, ("events", "rows")):
        case_id = str(event.get("case_id", ""))
        if case_id:
            availability.setdefault(case_id, _universe_record(event))
    _apply_official_ir_ticker_candidates(availability, official_rows)
    rows = build_availability_rows(availability)
    _write_csv(ROOT / args.out_csv, rows)
    write_text(ROOT / args.report, build_report(rows))
    print(f"IR/SEC availability matrix written: {len(rows)} row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
