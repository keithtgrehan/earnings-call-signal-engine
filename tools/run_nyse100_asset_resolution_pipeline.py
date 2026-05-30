#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
import sys
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from signal_engine.acquisition.asset_resolver import RESOLVED_ASSET_FIELDS, rank_asset_type, read_csv, resolve_official_ir_event_rows, write_csv
from signal_engine.acquisition.direct_asset_detector import detect_direct_asset
from signal_engine.acquisition.sec_resolver import resolve_sec_assets_for_rows
from tools.expand_nyse_universe_until_usable import EXPANSION_FIELDS, expand_nyse_universe, write_report as write_expansion_report
from tools.run_provider_asset_discovery import discover_provider_assets
from signal_engine.providers.base import ProviderConfig
from tools.user_authorized_ingest_common import DEFAULT_WORKSPACE

DEFAULT_ACQUISITION_DIR = ROOT / "data" / "acquisition"
DEFAULT_RETRIEVAL_DIR = ROOT / "data" / "retrieval"
REPORT_DIR = ROOT / "reports" / "acquisition"

PERMITTED_FIELDS = RESOLVED_ASSET_FIELDS + ["commit_allowed", "training_allowed", "eval_allowed"]


def _default_official(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return resolve_official_ir_event_rows(rows, max_pages_per_row=3, per_domain_delay_sec=0.25)


def _default_sec(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    sec_rows = read_csv(DEFAULT_ACQUISITION_DIR / "nyse_100_sec_event_index.csv")
    ticker_ciks = {row.get("ticker", ""): row.get("sec_company_ref", "0000000000").replace("CIK", "").zfill(10) for row in sec_rows}
    submissions = {
        row.get("ticker", ""): [
            {
                "form": "8-K",
                "filingDate": row.get("fiscal_year", ""),
                "accessionNumber": row.get("accession_number", ""),
                "items": "2.02" if row.get("item_202_or_exhibit_991") in {"true", "True", "1"} else "",
                "primaryDocument": Path(row.get("filing_url", "")).name,
                "exhibits": [{"document": Path(row.get("filing_url", "")).name, "description": "EX-99.1 earnings release metadata"}],
            }
        ]
        for row in sec_rows
        if row.get("ticker")
    }
    return resolve_sec_assets_for_rows(rows, ticker_ciks=ticker_ciks, submissions_by_ticker=submissions)


def _default_provider(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    import os

    return discover_provider_assets(rows=rows, config=ProviderConfig(env=dict(os.environ)))["candidates"]


def _dedupe_official_source_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Use one official IR traversal per case/source URL; each traversal can find transcript and audio."""
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (row.get("case_id", ""), row.get("source_url", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def _usable_pairs(candidates: list[dict[str, str]]) -> int:
    by_case: dict[str, set[str]] = defaultdict(set)
    for row in candidates:
        if row.get("download_allowed") != "true":
            continue
        if row.get("asset_type", "").startswith("transcript_"):
            by_case[row.get("case_id", "")].add("transcript")
        if row.get("asset_type", "").startswith("audio_"):
            by_case[row.get("case_id", "")].add("audio")
    return sum(1 for assets in by_case.values() if {"transcript", "audio"}.issubset(assets))


def _ranked(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(rows, key=lambda row: (row.get("case_id", ""), rank_asset_type(row.get("asset_type", "")), -float(row.get("confidence") or 0), row.get("resolved_asset_url", "")))


def _permitted(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    permitted = []
    for row in rows:
        if row.get("download_allowed") != "true":
            continue
        if not (row.get("asset_type", "").startswith("transcript_") or row.get("asset_type", "").startswith("audio_")):
            continue
        item = dict(row)
        item["commit_allowed"] = "false"
        item["training_allowed"] = "false"
        item["eval_allowed"] = "true"
        permitted.append({field: item.get(field, "") for field in PERMITTED_FIELDS})
    return permitted


def _write_report(path: Path, summary: dict[str, Any], candidates: list[dict[str, str]]) -> None:
    by_type = Counter(row.get("asset_type", "") for row in candidates)
    blockers = Counter(row.get("blocked_reason", "") for row in candidates if row.get("blocked_reason"))
    domains = Counter(row.get("asset_url_domain", "") for row in candidates if row.get("asset_url_domain"))
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Asset Resolution Summary",
        "",
        f"- Companies scanned: {summary['companies_scanned']}",
        f"- Calls scanned: {summary['calls_scanned']}",
        f"- Candidate rows: {summary['candidate_rows']}",
        f"- Usable candidate pairs: {summary['usable_candidate_pairs']}",
        f"- Permitted download rows: {summary['permitted_download_rows']}",
        f"- Direct transcript candidates: {sum(by_type[k] for k in ('transcript_text', 'transcript_pdf', 'transcript_html'))}",
        f"- Direct audio candidates: {sum(by_type[k] for k in ('audio_mp3', 'audio_m4a', 'audio_wav'))}",
        "",
        "## Top Domains",
    ]
    lines.extend(f"- {domain}: {count}" for domain, count in domains.most_common(10))
    lines.append("")
    lines.append("## Top Blockers")
    lines.extend(f"- {reason}: {count}" for reason, count in blockers.most_common(10))
    if not blockers:
        lines.append("- none")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_asset_resolution_pipeline(
    *,
    acquisition_dir: Path = DEFAULT_ACQUISITION_DIR,
    workspace: Path = DEFAULT_WORKSPACE,
    target_pairs: int = 100,
    start_year: int = 2025,
    years_back: int = 5,
    expand_until_exhausted: bool = False,
    max_workers: int = 1,
    official_resolver: Callable[[list[dict[str, str]]], list[dict[str, str]]] = _default_official,
    sec_resolver: Callable[[list[dict[str, str]]], list[dict[str, str]]] = _default_sec,
    provider_resolver: Callable[[list[dict[str, str]]], list[dict[str, str]]] = _default_provider,
    direct_detector: Callable[[dict[str, str]], dict[str, str]] = detect_direct_asset,
) -> dict[str, Any]:
    company_rows = read_csv(acquisition_dir / "nyse_100_company_universe.csv")
    target_rows = [
        row
        for row in read_csv(acquisition_dir / "nyse_100_5y_call_targets.csv")
        if str(row.get("exchange", "NYSE")).upper() == "NYSE" and start_year - years_back <= int(row.get("fiscal_year") or row.get("target_year") or start_year) <= start_year
    ]
    source_rows = _dedupe_official_source_rows(read_csv(acquisition_dir / "nyse_100_source_rights_review_queue.csv"))
    candidates = official_resolver(source_rows)
    candidates.extend(sec_resolver(target_rows))
    candidates.extend(provider_resolver(target_rows))
    detected = []
    for row in candidates:
        if row.get("download_allowed") == "true":
            detected.append(direct_detector(row))
        else:
            detected.append(row)
    ranked = _ranked(detected)
    permitted = _permitted(ranked)
    failures = [row for row in ranked if row.get("blocked_reason")]
    usable_pairs = _usable_pairs(ranked)
    write_csv(acquisition_dir / "nyse_100_ranked_asset_candidates.csv", ranked, RESOLVED_ASSET_FIELDS)
    write_csv(acquisition_dir / "nyse_100_asset_resolution_failures.csv", failures, RESOLVED_ASSET_FIELDS)
    write_csv(acquisition_dir / "nyse_100_user_authorized_permitted_downloads.csv", permitted, PERMITTED_FIELDS)
    write_csv(workspace / "_audit" / "ranked_asset_candidates.csv", ranked, RESOLVED_ASSET_FIELDS)
    if expand_until_exhausted or usable_pairs < target_pairs:
        expanded, expansion_summary = expand_nyse_universe(existing_companies=company_rows, candidate_companies=company_rows, usable_pairs=usable_pairs, target_pairs=target_pairs)
        write_csv(acquisition_dir / "nyse_expanded_candidate_universe.csv", expanded, EXPANSION_FIELDS)
        write_expansion_report(REPORT_DIR / "nyse_expansion_status.md", expansion_summary)
    summary = {
        "companies_scanned": len(company_rows),
        "calls_scanned": len(target_rows),
        "candidate_rows": len(ranked),
        "failure_rows": len(failures),
        "usable_candidate_pairs": usable_pairs,
        "permitted_download_rows": len(permitted),
        "target_pairs": target_pairs,
        "max_workers_requested": max_workers,
    }
    _write_report(REPORT_DIR / "asset_resolution_summary.md", summary, ranked)
    top_path = REPORT_DIR / "top_asset_candidates_for_download.md"
    top_path.write_text("# Top Asset Candidates For Download\n\n" + "\n".join(f"- {row['case_id']} {row['asset_type']} {row['resolved_asset_url']}" for row in permitted[:50]) + "\n", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run consolidated NYSE 100 asset resolution pipeline.")
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--target-pairs", type=int, default=100)
    parser.add_argument("--start-year", type=int, default=2025)
    parser.add_argument("--years-back", type=int, default=5)
    parser.add_argument("--expand-until-exhausted", action="store_true")
    parser.add_argument("--max-workers", type=int, default=1)
    args = parser.parse_args(argv)
    print(
        json.dumps(
            run_asset_resolution_pipeline(
                workspace=args.workspace,
                target_pairs=args.target_pairs,
                start_year=args.start_year,
                years_back=args.years_back,
                expand_until_exhausted=args.expand_until_exhausted,
                max_workers=args.max_workers,
            ),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
