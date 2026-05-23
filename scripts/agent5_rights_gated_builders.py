from __future__ import annotations

from collections import Counter
import csv
from pathlib import Path
import sys
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.agent5_acquisition import PILOT_COMPANIES, decide_source_use, stable_hash

FISCAL_PERIODS_5Y = [
    "2022_Q1",
    "2022_Q2",
    "2022_Q3",
    "2022_Q4",
    "2023_Q1",
    "2023_Q2",
    "2023_Q3",
    "2023_Q4",
    "2024_Q1",
    "2024_Q2",
    "2024_Q3",
    "2024_Q4",
    "2025_Q1",
    "2025_Q2",
    "2025_Q3",
    "2025_Q4",
    "2026_Q1",
    "2026_Q2",
    "2026_Q3",
    "2026_Q4",
]

IR_CANDIDATE_PATHS = [
    ("investor_relations_home", "https://investors.example.com/{ticker}/"),
    ("quarterly_results", "https://investors.example.com/{ticker}/quarterly-results"),
    ("earnings", "https://investors.example.com/{ticker}/earnings"),
    ("events_and_presentations", "https://investors.example.com/{ticker}/events-and-presentations"),
    ("sec_filings", "https://investors.example.com/{ticker}/sec-filings"),
    ("press_releases", "https://investors.example.com/{ticker}/press-releases"),
    ("webcast_archive", "https://investors.example.com/{ticker}/webcasts"),
    ("presentations_slides", "https://investors.example.com/{ticker}/presentations"),
]


def _load_targets(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return build_nyse_5y_universe(limit=500)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    rows = payload.get("targets") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError(f"{path} must contain a targets list")
    return rows


def write_yaml(path: Path, key: str, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump({key: rows}, sort_keys=False), encoding="utf-8")


def write_markdown(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines]) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_nyse_5y_universe(*, limit: int | None = 500) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ticker, company_name, sector in PILOT_COMPANIES:
        for fiscal_period in FISCAL_PERIODS_5Y:
            year = int(fiscal_period.split("_", 1)[0])
            rows.append(
                {
                    "case_id": f"nyse5y_{ticker.lower()}_{fiscal_period.lower()}",
                    "ticker": ticker,
                    "company_name": company_name,
                    "exchange": "NYSE",
                    "sector": sector,
                    "fiscal_period": fiscal_period,
                    "call_date_or_period": fiscal_period,
                    "lookback_year": year,
                    "event_identity_status": "target_slot_only",
                    "transcript_status": "unknown_not_ingested",
                    "audio_status": "unknown_not_ingested",
                    "video_status": "unknown_not_ingested",
                    "slides_status": "unknown_not_ingested",
                    "rights_status": "unknown",
                    "source_candidates_status": "not_reviewed",
                    "blocked_reason_code": "unknown_rights_blocked",
                    "manual_action": "review source terms, robots, official IR availability, and manual-local registration options",
                    "provenance_complete": False,
                }
            )
            if limit and len(rows) >= limit:
                return rows
    return rows


def build_official_ir_candidate_map(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for target in targets:
        ticker = str(target["ticker"]).lower()
        for candidate_kind, pattern in IR_CANDIDATE_PATHS:
            key = (str(target["case_id"]), ticker, candidate_kind)
            if key in seen:
                continue
            seen.add(key)
            candidate = {
                "case_id": target["case_id"],
                "ticker": str(target["ticker"]).upper(),
                "fiscal_period": target["fiscal_period"],
                "source_type": "official_ir_candidate",
                "candidate_kind": candidate_kind,
                "candidate_url_pattern": pattern.format(ticker=ticker),
                "raw_body_allowed": False,
                "raw_audio_allowed": False,
                "raw_video_allowed": False,
                "raw_slides_allowed": False,
                "terms_checked": False,
                "robots_checked": False,
                "blocked_reason_code": "rights_not_reviewed",
                "manual_action": "review terms/robots/source page before any raw use",
                "provenance_hash": stable_hash({"case_id": target["case_id"], "candidate_kind": candidate_kind, "ticker": ticker}),
            }
            rows.append(candidate)
    return rows


def build_sec_metadata_queue(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "ticker": target["ticker"],
            "case_id": target["case_id"],
            "cik_lookup_required": True,
            "target_forms": ["8-K", "10-Q", "10-K"],
            "fiscal_period": target["fiscal_period"],
            "fair_access_rate_limit_per_second": 10,
            "user_agent_required": True,
            "raw_body_allowed": False,
            "metadata_only": True,
            "blocked_reason_code": "sec_metadata_only_until_explicit_approval",
        }
        for target in targets
    ]


def build_webcast_metadata_queue(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "case_id": target["case_id"],
            "ticker": target["ticker"],
            "fiscal_period": target["fiscal_period"],
            "source_type": "youtube_metadata_only",
            "query_hint": f"{target['ticker']} {target['fiscal_period']} earnings call webcast",
            "raw_audio_allowed": False,
            "raw_video_allowed": False,
            "raw_transcript_allowed": False,
            "metadata_only": True,
            "blocked_reason_code": "youtube_raw_media_blocked_without_authorization",
        }
        for target in targets
    ]


def build_slides_availability_map(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "case_id": target["case_id"],
            "ticker": target["ticker"],
            "fiscal_period": target["fiscal_period"],
            "source_type": "official_ir_presentation_slides",
            "slides_status": "candidate_metadata_only",
            "raw_pdf_allowed": False,
            "download_attempted": False,
            "blocked_reason_code": "rights_not_reviewed",
            "manual_action": "review official IR presentation page terms before downloading or storing slides",
        }
        for target in targets
    ]


def build_source_availability_matrix(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in targets:
        rows.append(
            {
                "case_id": target["case_id"],
                "ticker": target["ticker"],
                "fiscal_period": target["fiscal_period"],
                "transcript_status": target.get("transcript_status", "unknown_not_ingested"),
                "audio_status": target.get("audio_status", "unknown_not_ingested"),
                "video_status": target.get("video_status", "unknown_not_ingested"),
                "slides_status": target.get("slides_status", "unknown_not_ingested"),
                "official_ir_candidate": True,
                "sec_candidate": True,
                "webcast_candidate": True,
                "youtube_metadata_only": True,
                "manual_local_registered": False,
                "vendor_blocked": True,
                "rights_status": "unknown",
                "blocked_reason_code": "unknown_rights_blocked",
                "provenance_complete": False,
                "next_manual_action": "review official IR/SEC/webcast availability and register manual-local path/hash if rights allow",
            }
        )
    return rows


def build_permitted_ingest_queue(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    allowed: list[dict[str, Any]] = []
    for candidate in candidates:
        decision = decide_source_use(candidate)
        if decision["decision"] != "allowed":
            continue
        if not any(candidate.get(flag) is True for flag in ("raw_body_allowed", "raw_transcript_allowed", "raw_audio_allowed", "raw_video_allowed", "raw_slides_allowed")):
            continue
        allowed.append({**candidate, "rights_decision": decision["decision"], "blocked_reason_code": decision["blocked_reason_code"]})
    return allowed


def summarize_blocked(rows: list[dict[str, Any]]) -> list[str]:
    counts = Counter(str(row.get("blocked_reason_code", "none")) for row in rows)
    return [f"- `{reason}`: `{count}`" for reason, count in sorted(counts.items())]
